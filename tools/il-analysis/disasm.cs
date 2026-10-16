using System;
using System.IO;
using System.Text;
using Mono.Cecil;
using Mono.Cecil.Cil;

class Disasm
{
    static string Esc(string s)
    {
        var sb = new StringBuilder();
        foreach (char c in s)
        {
            if (c == '"') sb.Append("\\\"");
            else if (c == '\\') sb.Append("\\\\");
            else if (c == '\n') sb.Append("\\n");
            else if (c == '\r') sb.Append("\\r");
            else if (c == '\t') sb.Append("\\t");
            else if (c < 0x20 || c > 0x7E) sb.Append("\\u" + ((int)c).ToString("x4"));
            else sb.Append(c);
        }
        return sb.ToString();
    }

    static void Main(string[] args)
    {
        // args: assembly, substring-of-method-name, [substring-of-type-name]
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        string msub = args[1];
        string tsub = args.Length > 2 ? args[2] : null;
        foreach (var module in asm.Modules)
        foreach (var type in module.GetTypes())
        {
            if (tsub != null && !type.FullName.Contains(tsub)) continue;
            foreach (var method in type.Methods)
            {
                if (method.Name == null || !method.Name.Contains(msub)) continue;
                if (!method.HasBody) continue;
                Console.WriteLine("=== " + type.FullName + "::" + method.Name + " ===");
                foreach (var ins in method.Body.Instructions)
                {
                    string operand = "";
                    if (ins.Operand != null) operand = ins.Operand.ToString();
                    Console.WriteLine("  IL_" + ins.Offset.ToString("x4") + ": " + ins.OpCode.Name + " " + Esc(operand));
                }
            }
        }
    }
}
