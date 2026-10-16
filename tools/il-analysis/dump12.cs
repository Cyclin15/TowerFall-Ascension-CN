using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump12 {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            foreach (var m in t.Methods) {
                if (!m.HasBody) continue;
                foreach (var ins in m.Body.Instructions) {
                    var mr = ins.Operand as MethodReference;
                    if (mr == null) continue;
                    if (mr.Name == "get_VersusTips" || mr.Name == "get_QuestTips" || mr.Name == "get_Tip") {
                        Console.WriteLine("{0}::{1} calls {2}", t.FullName, m.Name, mr.Name);
                        break;
                    }
                }
            }
        }
    }
}
