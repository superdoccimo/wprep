import mysql.connector
import logging
import os
import argparse
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import phpserialize

# .envファイルから環境変数を読み込む
load_dotenv()

# ログファイルの設定
logging.basicConfig(
    level=logging.DEBUG,  # ログレベルをDEBUGに設定
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wpurl_replace.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# コマンドライン引数の解析
parser = argparse.ArgumentParser(description='WordPress URL置換スクリプト')
parser.add_argument('--dry-run', action='store_true', help='実際の置換を行わずに確認だけ行う')
parser.add_argument('--old-url', required=True, help='置換元URL')
parser.add_argument('--new-url', required=True, help='置換先URL')
args = parser.parse_args()
logging.debug(f"コマンドライン引数: {args}")

# データベース接続設定
db_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
}
logging.debug(f"データベース設定: {db_config}")

# 以降の関数定義（省略せずにすべて記載）

# テーブルごとの主キーを取得する関数
def get_primary_key(table_name):
    primary_keys = {
        'wp_options': 'option_id',
        'wp_postmeta': 'meta_id',
        'wp_users': 'ID',
        'wp_posts': 'ID',
        'wp_commentmeta': 'meta_id',
        'wp_comments': 'comment_ID',
        'wp_links': 'link_id',
        'wp_term_taxonomy': 'term_taxonomy_id',
        'wp_termmeta': 'meta_id',
        'wp_terms': 'term_id',
        'wp_usermeta': 'umeta_id',
    }
    return primary_keys.get(table_name, 'id')  # デフォルトは'id'

# データベース接続を確立する関数
def connect_to_database():
    try:
        conn = mysql.connector.connect(**db_config, autocommit=True)
        logging.debug("データベースに接続しました")
        return conn
    except mysql.connector.Error as err:
        logging.error(f"データベース接続エラー: {err}")
        raise

# 全テーブルを取得する関数
def get_all_tables(cursor):
    cursor.execute("SHOW TABLES")
    return [table[0] for table in cursor.fetchall()]

# 特定のテーブルの全カラムを取得する関数
def get_columns(cursor, table_name):
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
    return cursor.fetchall()

# カラムがシリアライズされているかどうかを確認する関数
def is_column_serialized(table_name, column_name):
    serialized_columns = {
        'wp_options': ['option_value'],
        'wp_postmeta': ['meta_value'],
        # 他のシリアライズされたデータを含むテーブルとカラムを追加
    }
    return table_name in serialized_columns and column_name in serialized_columns[table_name]

# シリアライズされたデータのURLを置換し、再シリアライズする関数
def unserialize_replace_serialize(data, old_url, new_url):
    try:
        unserialized = phpserialize.loads(data.encode())
        if isinstance(unserialized, dict):
            for key, value in unserialized.items():
                if isinstance(value, bytes):
                    value_str = value.decode()
                    unserialized[key] = value_str.replace(old_url, new_url).encode()
        return phpserialize.dumps(unserialized).decode()
    except Exception:
        return data.replace(old_url, new_url)

# テーブル内の特定カラムに対してURLを置換する関数
def replace_url_in_table(table_name, column_name, old_url, new_url, dry_run):
    conn = connect_to_database()  # スレッドごとにデータベース接続
    cursor = conn.cursor()
    try:
        primary_key = get_primary_key(table_name)  # 主キーを取得
        if is_column_serialized(table_name, column_name):
            if dry_run:
                logging.info(f"Would replace serialized data in {table_name}.{column_name}")
                return 0
            else:
                sql = f"SELECT {primary_key}, `{column_name}` FROM `{table_name}` WHERE `{column_name}` LIKE %s"
                cursor.execute(sql, (f'%{old_url}%',))
                rows = cursor.fetchall()
                logging.debug(f"{table_name}.{column_name} で {len(rows)} 行が見つかりました")
                update_count = 0
                for row in rows:
                    id, data = row
                    new_data = unserialize_replace_serialize(data, old_url, new_url)
                    if new_data != data:
                        update_sql = f"UPDATE `{table_name}` SET `{column_name}` = %s WHERE {primary_key} = %s"
                        cursor.execute(update_sql, (new_data, id))
                        logging.debug(f"Updated row with ID {id} in {table_name}.{column_name}")
                        update_count += 1
                return update_count
        else:
            if dry_run:
                sql = f"SELECT COUNT(*) FROM `{table_name}` WHERE `{column_name}` LIKE %s"
                cursor.execute(sql, (f'%{old_url}%',))
                count = cursor.fetchone()[0]
                logging.info(f"Would replace {count} occurrences in {table_name}.{column_name}")
                return count
            else:
                sql_update = f"""
                UPDATE `{table_name}`
                SET `{column_name}` = REPLACE(`{column_name}`, %s, %s)
                WHERE `{column_name}` LIKE %s
                """
                cursor.execute(sql_update, (old_url, new_url, f'%{old_url}%'))
                affected_rows = cursor.rowcount
                logging.debug(f"Updated {affected_rows} rows in {table_name}.{column_name}")
                return affected_rows
    except mysql.connector.Error as err:
        logging.error(f"Error in {table_name}.{column_name}: {err}")
        return 0
    finally:
        cursor.close()
        conn.close()

def main():
    try:
        logging.debug("main関数を開始します")
        conn = connect_to_database()
        cursor = conn.cursor()

        tables = get_all_tables(cursor)
        logging.debug(f"取得したテーブル: {tables}")
        total_updates = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for table_name in tables:
                columns = get_columns(cursor, table_name)
                logging.debug(f"テーブル {table_name} のカラム: {columns}")
                for (column_name, column_type, _, _, _, _) in columns:
                    if 'char' in column_type or 'text' in column_type or 'varchar' in column_type:
                        logging.debug(f"{table_name}.{column_name} の処理を開始します")
                        future = executor.submit(
                            replace_url_in_table,
                            table_name,
                            column_name,
                            args.old_url,
                            args.new_url,
                            args.dry_run
                        )
                        futures.append(future)

            with tqdm(total=len(futures), desc="Processing") as pbar:
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        total_updates += result
                        pbar.update(1)
                    except Exception as e:
                        logging.error(f"Error during URL replacement: {e}", exc_info=True)

        print(f"Total updates: {total_updates}")
        if args.dry_run:
            print("Dry run completed. No changes were made.")
        else:
            print("URL置換が完了しました。")

    except Exception as e:
        logging.error(f"予期せぬエラーが発生しました: {e}", exc_info=True)
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            logging.debug("データベース接続を閉じました")

if __name__ == "__main__":
    main()