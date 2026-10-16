using System;
using System.Collections.Generic;
using Mono.Cecil;
using Mono.Cecil.Cil;

// Report candidate strings that are directly used as comparison operands:
// ldstr S followed (within 2 instrs) by op_Equality/op_Inequality/Contains.
class AfterCheck
{
    static void Main(string[] args)
    {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        var candidates = new HashSet<string>(System.IO.File.ReadAllLines(args[1]));
        foreach (var module in asm.Modules)
        foreach (var type in module.GetTypes())
        foreach (var method in type.Methods)
        {
            if (!method.HasBody) continue;
            var instrs = method.Body.Instructions;
            for (int i = 0; i < instrs.Count; i++)
            {
                string s = instrs[i].Operand as string;
                if (instrs[i].OpCode != OpCodes.Ldstr || s == null || !candidates.Contains(s)) continue;
                for (int j = i + 1; j < Math.Min(i + 3, instrs.Count); j++)
                {
                    MethodReference mr = instrs[j].Operand as MethodReference;
                    if (mr == null) continue;
                    if (mr.Name == "op_Equality" || mr.Name == "op_Inequality" || mr.Name == "Contains")
                    {
                        Console.WriteLine("EQ [" + s + "] " + type.FullName + "::" + method.Name);
                    }
                }
            }
        }
    }
}
