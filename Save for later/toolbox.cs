using System.Reflection;
using System.Security.Cryptography;
using System.Text.Json;
using Dapper;
using LoneWorkerRebuild.Repositories;

namespace LoneWorkerRebuild.Utilities;

internal static partial class Toolbox
{
    private static readonly JsonSerializerOptions _jsonSerializerOptionsPascalCase = new()
    {
        PropertyNamingPolicy = null,
    };
    public static JsonSerializerOptions JsonSerializerOptionsPascalCase => _jsonSerializerOptionsPascalCase;

    private static readonly JsonSerializerOptions _jsonSerializerOptionsPrettify = new()
    {
        WriteIndented = true,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    };
    public static JsonSerializerOptions JsonSerializerOptionsPrettify => _jsonSerializerOptionsPrettify;

    public static string ObjectToJson(object? input, JsonSerializerOptions? options = null)
    {
        // if input is json, deserialize it first
        if (input is string json && json.TrimStart().StartsWith('{'))
            input = JsonSerializer.Deserialize<string>(json, Toolbox.JsonSerializerOptionsPrettify);

        // if input is null or empty, return empty string
        if (input == null || (input is string s && string.IsNullOrWhiteSpace(s)))
            return string.Empty;

        options ??= Toolbox.JsonSerializerOptionsWriteIndented;

        return JsonSerializer.Serialize(input, options);
    }

    public static string PrettifyJson(string json)
    {
        return JsonSerializer.Serialize(JsonDocument.Parse(json), Toolbox.JsonSerializerOptionsPrettify);
    }

    public static TimeZoneInfo? GetTimezoneForAustralianState(string? state)
    {
        if (string.IsNullOrWhiteSpace(state))
            return null;

        return state switch
        {
            "ACT" => TimeZoneInfo.FindSystemTimeZoneById("Australia/Sydney"),
            "NSW" => TimeZoneInfo.FindSystemTimeZoneById("Australia/Sydney"),
            "NT" => TimeZoneInfo.FindSystemTimeZoneById("Australia/Darwin"),
            "QLD" => TimeZoneInfo.FindSystemTimeZoneById("Australia/Brisbane"),
            "SA" => TimeZoneInfo.FindSystemTimeZoneById("Australia/Adelaide"),
            "TAS" => TimeZoneInfo.FindSystemTimeZoneById("Australia/Hobart"),
            "VIC" => TimeZoneInfo.FindSystemTimeZoneById("Australia/Melbourne"),
            "WA" => TimeZoneInfo.FindSystemTimeZoneById("Australia/Perth"),
            _ => null,
        };
    }

    public static bool IsValidName(string? name)
    {
        if (string.IsNullOrWhiteSpace(name))
            return false;

        bool hasLetter = false;

        // Allow letters, spaces, hyphens, underscores, apostrophes, periods, and commas
        foreach (char c in name)
        {
            if (char.IsLetter(c))
                hasLetter = true;
            else if (c != ' ' && c != '-' && c != '_' && c != '\'' && c != '.' && c != ',')
                return false;
        }

        return hasLetter;
    }

    public static bool IsValidAustralianState(string? state)
    {
        if (string.IsNullOrWhiteSpace(state))
            return false;

        switch (state)
        {
            case "ACT":
            case "NSW":
            case "NT":
            case "QLD":
            case "SA":
            case "TAS":
            case "VIC":
            case "WA":
                return true;
        }
        return false;
    }

    public static bool IsValidLocationType(string? locationType)
    {
        if (string.IsNullOrWhiteSpace(locationType))
            return false;

        switch (locationType)
        {
            case "None":
            case "Free Text":
            case "Address Search":
            case "Database":
            case "Database+Unlisted":
                return true;
        }
        return false;
    }

    public static bool IsValidSendLogOutConfirmationType(string? sendLogOutConfirmationType)
    {
        if (string.IsNullOrWhiteSpace(sendLogOutConfirmationType))
            return false;

        if (sendLogOutConfirmationType == "0" // Nothing to send
            || sendLogOutConfirmationType == "1" // Send SMS to Original Duty Officer Tel number 1
            || sendLogOutConfirmationType == "2") // Send SMS to every mobile number we have called
        {
            return true;
        }

        // Check if content is a list of email addresses
        string[] emailAddresses = sendLogOutConfirmationType.Split(EmailsSeparator, StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries);

        // Validate each email address
        foreach (string emailAddress in emailAddresses)
        {
            if (!IsValidEmail(emailAddress))
            {
                return false;
            }

            if (emailAddress.EndsWith("@sms.oraclecms.com"))
            {
                if (!IsValidSmsEmailAddress(emailAddress))
                {
                    return false;
                }
            }
        }

        return true;
    }

    public static bool IsValidSmsEmailAddress(string? email)
    {
        // Validate email is not blank
        if (string.IsNullOrWhiteSpace(email))
            return false;

        // Validate length (phone number is 11 digits long)
        if (email.Length != 11 + "@sms.oraclecms.com".Length)
        {
            return false;
        }

        // Must be a mobile number
        if (!email.StartsWith("614"))
        {
            return false;
        }

        // Must end in "@sms.oraclecms.com"
        if (!email.EndsWith("@sms.oraclecms.com"))
        {
            return false;
        }

        return true;
    }

    public static string? TrimPhoneNumber(string? phoneNumber, bool keepPlus = true)
    {
        if (string.IsNullOrWhiteSpace(phoneNumber))
            return null;

        return new string(phoneNumber
            .Where((c, i) => char.IsDigit(c) || (keepPlus && c == '+' && i == 0))
            .ToArray());
    }

    public static string? CleanPhoneNumber(string? number)
    {
        if (string.IsNullOrWhiteSpace(number))
            return null;

        // Remove all non-digit characters
        return new string(number.Where(char.IsDigit).ToArray());
    }

    public static string AusMobileToInternationalFormat(string number)
    {
        if (!IsValidAusMobileNumber(number))
            return number;

        string digitsOnly = CleanPhoneNumber(number)!;

        if (digitsOnly.StartsWith("04"))
        {
            // Replace leading '0' with "61"
            digitsOnly = "61" + digitsOnly[1..];
        }
        return digitsOnly;
    }

    public static bool IsValidAusMobileNumber(string? number)
    {
        string digitsOnly = CleanPhoneNumber(number)!;
        return (digitsOnly.StartsWith("04") && digitsOnly.Length == 10) ||
            (digitsOnly.StartsWith("614") && digitsOnly.Length == 11);
    }

    public static bool IsValidPhoneNumber(string? phoneNumber)
    {
        if (string.IsNullOrWhiteSpace(phoneNumber))
            return false;

        // Check for invalid characters
        char[] allowedNonDigitChars = ['+', '(', ')', '-', ' '];
        if (phoneNumber.Any(c => !char.IsDigit(c) && !allowedNonDigitChars.Contains(c)))
            return false;

        // Get digits only
        string? digitsOnly = TrimPhoneNumber(phoneNumber, false);
        if (string.IsNullOrWhiteSpace(digitsOnly))
            return false;

        // Check length
        if (digitsOnly.Length is < 6 or > 15)
            return false;

        // Handle Australian numbers
        if (phoneNumber.StartsWith('0') || digitsOnly.StartsWith('1'))
        {
            string[] ausPrefixes = { "02", "03", "04", "07", "08", "1300", "1800" };
            if ((digitsOnly.Length == 10 && ausPrefixes.Any(ac => digitsOnly.StartsWith(ac)))
                || (digitsOnly.Length == 6 && digitsOnly.StartsWith("13")))
                return true;
        }

        // Handle international numbers
        if (phoneNumber.Trim().StartsWith('+') || (digitsOnly.Length >= 8 && !digitsOnly.StartsWith('0')))
            return HasValidInternationalPrefix(digitsOnly);

        return false;
    }

    private static bool HasValidInternationalPrefix(string digitsOnly)
    {
        // For international numbers, first digit must not be '0'
        if (digitsOnly.StartsWith('0'))
            return false;

        // Check against known valid prefixes
        return CountryCallingPrefixes.SortedMostLikely
            .Any(prefix => digitsOnly.StartsWith(prefix));
    }

    public static string GetSqlString(CommandDefinition command)
    {
        return GetSqlString(command.CommandText, (DynamicParameters?)command.Parameters);
    }

    public static string GetSqlString(string sql, DynamicParameters? parameters = null)
    {
        return parameters == null ? sql : $"{DynamicParametersToSql(parameters)}{sql}";
    }

    public static string GetSqlExceptionString(SqlException ex, CommandDefinition command)
    {
        string sql = GetSqlString(command);
        return GetSqlExceptionString(ex, sql);
    }

    public static string GetSqlExceptionString(SqlException ex, string? sql = null)
    {
        StringBuilder errorStr = new();
        List<int> errorLines = [];

        string newLine = Environment.NewLine;
        string twoNewLines = Environment.NewLine + Environment.NewLine;

        errorStr.Append("SQL Exception details:");

        if (ex.Errors.Count == 0)
        {
            errorStr.Append(twoNewLines + "  No additional information.");
        }
        else
        {
            for (int i = 0; i < ex.Errors.Count; i++)
            {
                errorStr.Append(twoNewLines + "  SQL Error #" + (i + 1) + " of " + ex.Errors.Count + newLine +
                    "  Message: " + ex.Errors[i].Message + newLine +
                    "  Error Number: " + ex.Errors[i].Number + newLine +
                    "  Line Number: " + ex.Errors[i].LineNumber + newLine +
                    "  Source: " + ex.Errors[i].Source + newLine +
                    "  Procedure: " + ex.Errors[i].Procedure);
                errorLines.Add(ex.Errors[i].LineNumber);
            }
        }


        if (ex.Number is (-2146893019) or 18456 or 53)
        {
            return errorStr.ToString();
        }

        if (!string.IsNullOrWhiteSpace(sql))
        {
            errorStr.Append(twoNewLines + "SQL Query:");
            errorStr.Append(twoNewLines + Indent(AddLineNumbers(sql, errorLines)));
        }

        return errorStr.ToString();
    }

    public static string AddLineNumbers(string input, List<int>? errorLines = null)
    {
        if (string.IsNullOrEmpty(input))
            return string.Empty;

        string[] lines = input.Split(Environment.NewLine);
        int lineCount = lines.Length;
        int numberWidth = lineCount.ToString().Length;

        // Use a HashSet for efficient lookup if errorLines is provided
        HashSet<int>? errorLineSet = errorLines is not null ? new(errorLines) : null;

        StringBuilder result = new();
        for (int i = 0; i < lineCount; i++)
        {
            // Add '>' if this is one of the error lines (1-based index)
            string marker = (errorLineSet is not null && errorLineSet.Contains(i + 1)) ? "> " : "  ";
            result.Append($"{marker}{(i + 1).ToString().PadLeft(numberWidth)}| {lines[i]}{Environment.NewLine}");
        }

        return result.ToString().TrimEnd();
    }

    public static string Indent(string input, int indentWidth = 2)
    {
        if (string.IsNullOrEmpty(input))
            return string.Empty;

        string indent = new(' ', indentWidth);
        string[] lines = input.Split(Environment.NewLine);

        StringBuilder result = new();
        foreach (string line in lines)
        {
            result.Append($"{indent}{line}{Environment.NewLine}");
        }
        return result.ToString().TrimEnd();
    }

    // eg.
    // ("A2", "A1") => "A2
    // ("A2", "A1:C1") => "A2:C2"
    // ("A2", "A1:C1" data(.Rows.Count = 3)(.Columns.Count = 2) => "A2:B4"
    public static string GetCellRange(string startCell, string filterRange, DataTable? data = null)
    {
        if (string.IsNullOrEmpty(startCell) || string.IsNullOrEmpty(filterRange))
            return string.Empty;

        string[] filterParts = filterRange.Split(':');

        ExcelCellAddress start = new(startCell);
        ExcelCellAddress filterStart = new(filterParts[0]);
        ExcelCellAddress? filterEnd = filterParts.Length == 2 ? new(filterParts[1]) : null;
        ExcelCellAddress? end = null;

        // Calculate the end cell based on the filter range
        if (filterEnd is not null)
        {
            int endRow = filterEnd.Row - filterStart.Row + start.Row;
            int endColumn = filterEnd.Column - filterStart.Column + start.Column;

            // Adjust end cell if data is provided
            if (data is not null && data.Rows.Count > 0)
            {
                endRow = start.Row + data.Rows.Count - 1;
                endColumn = start.Column + data.Columns.Count - 1;
            }

            end = new($"{ExcelCellAddress.GetColumnLetter(endColumn)}{endRow}");
        }

        return $"{start.Address}{(end is not null ? $":{end.Address}" : "")}";
    }

    public static string DataTableToPrettyString(DataTable table)
    {
        if (table == null)
            return "";

        StringBuilder result = new();

        // Calculate max column widths (including headers)
        int colCount = table.Columns.Count;
        int[] colWidths = new int[colCount];

        // Set initial widths based on column names
        for (int i = 0; i < colCount; i++)
            colWidths[i] = table.Columns[i].ColumnName.Length;

        // Check all rows to determine max content widths
        foreach (DataRow row in table.Rows)
        {
            for (int i = 0; i < colCount; i++)
            {
                string? text = row.IsNull(i) ? "null" : row[i].ToString();
                colWidths[i] = Math.Max(colWidths[i], text?.Length ?? 0);
            }
        }

        // Append headers
        for (int i = 0; i < colCount; i++)
            result.Append(table.Columns[i].ColumnName.PadRight(colWidths[i] + 2));
        result.AppendLine();

        // Append separator line
        for (int i = 0; i < colCount; i++)
            result.Append(new string('-', colWidths[i]) + "  ");
        result.AppendLine();

        // Append rows
        foreach (DataRow row in table.Rows)
        {
            for (int i = 0; i < colCount; i++)
            {
                string? text = row.IsNull(i) ? "null" : row[i].ToString();
                result.Append((text ?? "null").PadRight(colWidths[i] + 2));
            }
            result.AppendLine();
        }

        return result.ToString();
    }

    public static string GetExcelSheetDetails(ExcelPackage package)
    {
        if (package == null)
            return "";

        // Get the workbook
        ExcelWorkbook workbook = package.Workbook;

        StringBuilder result = new();

        // Iterate through all worksheets
        foreach (ExcelWorksheet? worksheet in workbook.Worksheets)
        {
            // Get the sheet name (tab name)
            string sheetName = worksheet.Name;

            // Get the internal ID (SheetID)
            int sheetId = worksheet.Index;

            result.AppendLine($"{sheetId.ToString().PadLeft(2)} - '{sheetName}'");
        }

        return result.ToString();
    }

    public static string GenerateShortId(int length = LookupRepository.ShortIdLength)
    {
        const string chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
        return new string(Enumerable.Range(0, length)
            .Select(_ => chars[RandomNumberGenerator.GetInt32(chars.Length)])
            .ToArray());
        // TODO: (Suggestion) Check for recognizable or rude words
    }

    public static List<string> SplitList(string? str)
    {
        if (string.IsNullOrEmpty(str))
            return [];

        List<string> list = [.. str?.Split([',', ';'], StringSplitOptions.TrimEntries | StringSplitOptions.RemoveEmptyEntries)];
        return list.Distinct().ToList();
    }

    public static TTarget? ConvertObject<TSource, TTarget>(TSource? source, TTarget? target = null, bool includeNulls = false) where TTarget : class, new()
    {
        // If no source provided, return the target as is
        if (source is null)
            return target;

        // Create new target object with matching properties from source
        JsonSerializerOptions options = new() { PropertyNameCaseInsensitive = true };
        string sourceJson = JsonSerializer.Serialize(source, options);
        TTarget? newTarget = JsonSerializer.Deserialize<TTarget>(sourceJson, options);
        if (newTarget is null)
            return target;

        // If no target provided, return the new target object
        if (target is null)
            return newTarget;

        // Track which properties existed in the source JSON
        using JsonDocument doc = JsonDocument.Parse(sourceJson);
        JsonElement sourceRoot = doc.RootElement;
        HashSet<string> sourceProps = sourceRoot.EnumerateObject().Select(p => p.Name).ToHashSet(StringComparer.OrdinalIgnoreCase);

        // Copy matching properties into provided target
        foreach (PropertyInfo prop in typeof(TTarget).GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            if (!prop.CanRead || !prop.CanWrite)
                continue;

            // Only update if the source included the property
            if (!sourceProps.Contains(prop.Name))
                continue;

            object? value = prop.GetValue(newTarget);

            if (includeNulls || value is not null)
            {
                try
                {
                    prop.SetValue(target, value);
                }
                catch (Exception ex)
                {
                    Log.Error($"Could not set property {prop.Name} on target object\n{ex}");
                }
            }
        }

        return target;
    }
}
