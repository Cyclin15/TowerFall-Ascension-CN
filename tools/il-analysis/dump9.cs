using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump9 {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            if (t.Name != "TFGame") continue;
            foreach (var f in t.Fields) Console.WriteLine("FIELD {0} {1}", f.FieldType, f.Name);
            foreach (var m in t.Methods) {
                if (m.Name != "get_Font" && m.Name != "LoadContent") continue;
                if (!m.HasBody) continue;
                Console.WriteLine("METHOD {0}", m.Name);
                foreach (var ins in m.Body.Instructions)
                    Console.WriteLine("  IL_{0:x4}: {1} {2}", ins.Offset, ins.OpCode, ins.Operand);
            }
        }
    }
}
