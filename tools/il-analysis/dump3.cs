using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump3 {
    static void Disasm(MethodDefinition m) {
        if (!m.HasBody) { Console.WriteLine("    (no body)"); return; }
        foreach (var ins in m.Body.Instructions)
            Console.WriteLine("    IL_{0:x4}: {1} {2}", ins.Offset, ins.OpCode, ins.Operand);
    }
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            bool isSF = t.FullName == "Microsoft.Xna.Framework.Graphics.SpriteFont";
            if (!isSF) continue;
            Console.WriteLine("=== {0} ===", t.FullName);
            foreach (var f in t.Fields)
                Console.WriteLine("  FIELD {0} {1}", f.FieldType, f.Name);
            foreach (var p in t.Properties)
                Console.WriteLine("  PROP {0} {1}", p.PropertyType, p.Name);
            foreach (var m in t.Methods) {
                if (m.Name != "MeasureString" && m.Name != "GetIndexForCharacter"
                 && m.Name != "InternalDrawString" && m.Name != "DrawString"
                 && m.Name != "DrawInto" && m.Name != ".ctor") continue;
                if (!m.HasBody) continue;
                Console.WriteLine("  METHOD {0}", m.FullName);
                Disasm(m);
            }
        }
    }
}
