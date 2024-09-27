# WordPress URL Replace Script

## Purpose
This script is a tool for efficiently replacing URLs in WordPress databases. It allows for safe URL replacement, including serialized data, even in environments where WP-CLI is not available.

## Features
- URL Replacement: Replaces old URLs with new ones in the database.
- Serialized Data Handling: Properly replaces URLs in serialized data.
- Dry-run Mode: Allows checking the extent of changes before actual modification.
- Parallel Processing: Efficiently processes multiple tables and columns.
- Detailed Logging: Records replacement progress and results in `wpurl_replace.log`.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/superdoccimo/wprep.git
   cd wprep
   ```

2. Install required Python libraries:
   ```bash
   pip install mysql-connector-python python-dotenv phpserialize tqdm
   ```

## Usage

1. **Set Environment Variables**  
   Create a `.env` file with your database connection information:

   ```
   DB_USER=username
   DB_PASSWORD=yourpassword
   DB_HOST=localhost
   DB_NAME=yourdbname
   ```

2. **Run the Script**  
   Execute the following command, specifying the `old-url` and `new-url` arguments:

   ```bash
   python wp-url-replace.py --old-url http://oldurl.com --new-url http://newurl.com
   ```

3. **Dry-run Mode**  
   To simulate changes without actually modifying the database, use the `--dry-run` option:

   ```bash
   python wp-url-replace.py --old-url http://oldurl.com --new-url http://newurl.com --dry-run
   ```

## Error Handling

The script logs error messages and handles various scenarios, including MySQL connection errors and replacement process errors. Check the `wpurl_replace.log` file for detailed error information and troubleshooting.

## Prerequisites

- Python 3.6+
- MySQL database
- Required Python libraries (mysql-connector, dotenv, phpserialize, tqdm)
- Properly configured `.env` file

## Data Backup

**IMPORTANT**: Always backup your database before running this script. This is crucial to prevent data loss due to operational mistakes.

### Example of using mysqldump for backup:

```bash
mysqldump -u username -p database_name > backup.sql
```

## Post-Execution Verification

After running the script, it's important to verify that the replacements were correctly applied. Use SQL queries to check specific tables and columns.

### Example verification query:

```sql
SELECT * FROM wp_options WHERE option_value LIKE '%new_url%';
```

## Security Considerations

When using scripts that access databases, pay attention to security:

- Set appropriate permissions for the script file.
- Limit database user privileges to the minimum necessary (e.g., READ and WRITE permissions only).

## Performance Notes

- For large databases, the script may take considerable time to run.
- Resource usage (CPU, memory) may be high during execution, especially with parallel processing.

## Troubleshooting

Common issues and their solutions:

1. **Database Connection Error**: Ensure your `.env` file contains correct database credentials.
2. **Permission Denied**: Check that you have the necessary permissions to execute the script and access the database.
3. **Memory Exhaustion**: For very large databases, you may need to increase your system's memory allocation to Python.

## Limitations

- The script may not handle extremely complex serialized data structures.
- It does not modify URLs in file paths or custom database tables not typical to WordPress.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature.
3. Make your changes and test thoroughly.
4. Submit a pull request with a clear description of your changes.

## Detailed Explanation

**English**  
[https://betelgeuse.work/archives/8282](https://betelgeuse.work/archives/8282)

**Japanese**  
[https://minokamo.tokyo/2024/09/28/8016/](https://minokamo.tokyo/2024/09/28/8016/)

## Videos

**English**  
[https://youtu.be/Rd1NwwLfyn8](https://youtu.be/Rd1NwwLfyn8)

**Japanese**  
[https://youtu.be/MjQ9jPClsaY](https://youtu.be/MjQ9jPClsaY)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Version History

- 1.0.0 (2024-09-26): Initial release
- 1.0.1 (2024-09-27): Added parallel processing feature

## Contact

If you have any questions or feedback, please open an issue on the GitHub repository.
