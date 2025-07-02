public static string PrettifyObject(object obj, int indentLevel = 0)
{
    if (obj == null)
        return "null";

    // Indentation helpers
    const int size = 2;
    string indent = new(' ', indentLevel * size);
    static string indents(int n) => new(' ', n * size);

    // Strings
    if (obj is string str)
    {
        if (str.Contains('\n'))
        {
            string[] lines = str.Split('\n');
            string multiline = string.Join("\n" + indents(2), lines.Select(line => line.TrimEnd()));
            return $"\"\"\"\n{indents(2)}{multiline}\"\"\"";
        }
        else
        {
            return $"\"{str}\"";
        }
    }

    // Primitives
    if (obj is bool b)
    {
        return b.ToString().ToLower(); // true / false
    }

    if (obj is Guid guid)
    {
        return $"\"{guid}\"";
    }

    if (obj is int or long or double or float or decimal)
    {
        return obj.ToString()!;
    }

    // JValue
    if (obj is JValue jVal)
    {
        return PrettifyObject(jVal.Value ?? "null", indentLevel);
    }

    // JObject
    if (obj is JObject jObj)
    {
        Dictionary<string, object>? oDict = jObj.ToObject<Dictionary<string, object>>();
        return PrettifyObject(oDict ?? new Dictionary<string, object>(), indentLevel);
    }

    // JArray
    if (obj is JArray jArr)
    {
        List<object>? aList = jArr.ToObject<List<object>>();
        return PrettifyObject(aList ?? [], indentLevel);
    }

    // Dictionary<string, string>
    if (obj is IDictionary<string, string> stringDict)
    {
        IEnumerable<string> lines = stringDict.Select(
            kv => $"{indent}  {kv.Key}: {PrettifyObject(kv.Value, indentLevel + 1)}");
        return $"{{\n{string.Join(",\n", lines)}\n{indent}}}";
    }

    // Dictionary<string, object> and JObject
    if (obj is IDictionary<string, object> dict)
    {
        IEnumerable<string> lines = dict.Select(
            kv => $"{indent}  {kv.Key}: {PrettifyObject(kv.Value, indentLevel + 1)}");
        return $"{{\n{string.Join(",\n", lines)}\n{indent}}}";
    }

    // lists/arrays
    if (obj is IEnumerable<object> list)
    {
        IEnumerable<string> items = list.Select(item => PrettifyObject(item, indentLevel + 1));
        return $"[\n{indent}  {string.Join(",\n" + indent + "  ", items)}\n{indent}]";
    }

    // Reflect over POCOs
    Dictionary<string, object?> props = obj.GetType()
        .GetProperties(BindingFlags.Public | BindingFlags.Instance)
        .Where(p => p.GetIndexParameters().Length == 0)
        .ToDictionary(p => p.Name, p => p.GetValue(obj));

    return PrettifyObject(props, indentLevel);
}