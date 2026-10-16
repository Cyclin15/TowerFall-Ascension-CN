using System;
using System.Collections.Generic;
using Mono.Cecil;
using Mono.Cecil.Cil;

class GetStatCheck
{
    static void Main(string[] args)
    {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var module in asm.Modules)
        foreach (var type in module.GetTypes())
        foreach (var method in type.Methods)
        {
            if (!method.HasBody) continue;
            var instrs = method.Body.Instructions;
            for (int i = 0; i < instrs.Count; i++)
            {
                MethodReference mr = instrs[i].Operand as MethodReference;
                if (mr == null) continue;
                if (mr.Name == "GetStat" || mr.Name == "SetStat" || mr.Name == "SetAchievement" || mr.Name == "StoreStats")
                {
                    // look back for the nearest ldstr
                    for (int j = i - 1; j >= Math.Max(0, i - 6); j--)
                    {
                        if (instrs[j].OpCode == OpCodes.Ldstr)
                        {
                            Console.WriteLine(mr.Name + " [" + instrs[j].Operand + "] " + type.FullName + "::" + method.Name);
                            break;
                        }
                    }
                }
            }
        }
    }
}
