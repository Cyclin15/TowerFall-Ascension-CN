using System;
using System.Collections.Generic;
using Mono.Cecil;
using Mono.Cecil.Cil;

// For each candidate display string, report methods that use it via ldstr
// AND also call string equality / Contains / set_Item nearby (key-usage risk).
class EqCheck
{
    static void Main(string[] args)
    {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        var candidates = new HashSet<string>(
            System.IO.File.ReadAllLines(args[1]));
        foreach (var module in asm.Modules)
        foreach (var type in module.GetTypes())
        foreach (var method in type.Methods)
        {
            if (!method.HasBody) continue;
            var used = new HashSet<string>();
            bool eqCall = false;
            foreach (var ins in method.Body.Instructions)
            {
                if (ins.OpCode == OpCodes.Ldstr)
                {
                    string s = ins.Operand as string;
                    if (s != null && candidates.Contains(s)) used.Add(s);
                }
                MethodReference mr = ins.Operand as MethodReference;
                if (mr != null)
                {
                    string n = mr.Name;
                    if (n == "op_Equality" || n == "op_Inequality" || n == "Contains"
                        || n == "set_Item" || n == "Equals" || n == "CompareTo" || n == "StartsWith" || n == "EndsWith")
                    {
                        if (mr.DeclaringType != null &&
                            (mr.DeclaringType.Name == "String" ||
                             mr.DeclaringType.FullName.Contains("Dictionary") ||
                             mr.DeclaringType.FullName.Contains("List`1")))
                            eqCall = true;
                    }
                }
            }
            foreach (var s in used)
            {
                if (eqCall)
                    Console.WriteLine("FLAG [" + s + "] " + type.FullName + "::" + method.Name);
            }
        }
    }
}
