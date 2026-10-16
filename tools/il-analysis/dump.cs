using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Mono.Cecil;
using Mono.Cecil.Cil;

class Dump
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
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        var seen = new Dictionary<string, StringBuilder>();
        using (var outw = new StreamWriter(args[1], false, new UTF8Encoding(false)))
        {
            foreach (var module in asm.Modules)
            {
                foreach (var type in module.GetTypes())
                {
                    foreach (var method in type.Methods)
                    {
                        if (!method.HasBody) continue;
                        foreach (var ins in method.Body.Instructions)
                        {
                            if (ins.OpCode == OpCodes.Ldstr)
                            {
                                string s = (string)ins.Operand;
                                string key = type.FullName + "::" + method.Name;
                                outw.WriteLine("{\"type\":\"" + Esc(type.FullName) + "\",\"method\":\"" + Esc(method.Name) + "\",\"str\":\"" + Esc(s) + "\"}");
                            }
                        }
                    }
                }
            }
        }
        Console.WriteLine("done");
    }
}
