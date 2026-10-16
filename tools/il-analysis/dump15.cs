using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump15 {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            foreach (var m in t.Methods) {
                if (!m.HasBody) continue;
                foreach (var ins in m.Body.Instructions) {
                    var fr = ins.Operand as FieldReference;
                    if (fr == null) continue;
                    if (fr.DeclaringType != null && fr.DeclaringType.Name == "VersusTipInfo" && fr.Name == "TextA") {
                        Console.WriteLine("{0}::{1}", t.FullName, m.Name);
                        break;
                    }
                }
            }
        }
    }
}
