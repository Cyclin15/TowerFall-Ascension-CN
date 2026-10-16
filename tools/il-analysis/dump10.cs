using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump10 {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            foreach (var m in t.Methods) {
                if (!m.HasBody) continue;
                foreach (var ins in m.Body.Instructions)
                    if (ins.OpCode == OpCodes.Ldstr) {
                        string s = (string)ins.Operand;
                        if (s.IndexOf("Tips", StringComparison.OrdinalIgnoreCase) >= 0
                         || s.IndexOf("OpenSans", StringComparison.OrdinalIgnoreCase) >= 0)
                            Console.WriteLine("{0}::{1}: {2}", t.FullName, m.Name, s);
                    }
            }
        }
    }
}
