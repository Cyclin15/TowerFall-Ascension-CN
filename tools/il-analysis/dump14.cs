using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump14 {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            foreach (var m in t.Methods) {
                if (!m.HasBody) continue;
                foreach (var ins in m.Body.Instructions) {
                    var mr = ins.Operand as MethodReference;
                    if (mr == null) continue;
                    if (mr.DeclaringType != null && mr.DeclaringType.Name == "VersusTipInfo"
                        && (mr.Name == "get_TextA" || mr.Name == "get_TextB")) {
                        Console.WriteLine("{0}::{1}", t.FullName, m.Name);
                        break;
                    }
                }
            }
        }
    }
}
