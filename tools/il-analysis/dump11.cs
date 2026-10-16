using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump11 {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            if (t.FullName != "TowerFall.GameTips" && t.Name != "TipImage" && t.Name != "TipText") continue;
            Console.WriteLine("=== {0} (base {1}) ===", t.FullName, t.BaseType);
            foreach (var f in t.Fields) Console.WriteLine("  FIELD {0} {1}", f.FieldType, f.Name);
            foreach (var m in t.Methods) {
                if (!m.HasBody) continue;
                Console.WriteLine("  METHOD {0}", m.Name);
                foreach (var ins in m.Body.Instructions)
                    Console.WriteLine("    IL_{0:x4}: {1} {2}", ins.Offset, ins.OpCode, ins.Operand);
            }
        }
    }
}
