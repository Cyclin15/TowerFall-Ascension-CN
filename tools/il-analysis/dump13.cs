using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump13 {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            if (t.FullName != "TowerFall.ArchivesTipsPage") continue;
            foreach (var m in t.Methods) {
                if (m.Name != "Render" || !m.HasBody) continue;
                foreach (var ins in m.Body.Instructions) {
                    var mr = ins.Operand as MethodReference;
                    if (ins.OpCode == OpCodes.Call || ins.OpCode == OpCodes.Callvirt)
                        if (mr != null && (mr.Name.Contains("Text") || mr.Name.Contains("Font") || mr.Name.Contains("Measure")))
                            Console.WriteLine("IL_{0:x4}: {1} {2}", ins.Offset, ins.OpCode, mr.FullName);
                }
            }
        }
    }
}
