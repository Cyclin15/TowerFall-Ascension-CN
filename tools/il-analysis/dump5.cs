using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump5 {
    static void Disasm(MethodDefinition m) {
        foreach (var ins in m.Body.Instructions)
            Console.WriteLine("    IL_{0:x4}: {1} {2}", ins.Offset, ins.OpCode, ins.Operand);
    }
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            if (t.FullName != "Monocle.Text" && t.FullName != "Monocle.TextRenderer") continue;
            Console.WriteLine("=== {0} (base {1}) ===", t.FullName, t.BaseType);
            foreach (var f in t.Fields) Console.WriteLine("  FIELD {0} {1}", f.FieldType, f.Name);
            foreach (var m in t.Methods) {
                if (!m.HasBody) continue;
                bool usesFont = false;
                foreach (var ins in m.Body.Instructions) {
                    var op = ins.Operand as string;
                    var mr = ins.Operand as MethodReference;
                    if (mr != null && (mr.Name == "MeasureString" || mr.Name == "DrawString" || mr.Name=="get_DefaultCharacter" || mr.FullName.Contains("SpriteFont")))
                        usesFont = true;
                }
                if (!usesFont && m.Name != "Render" && m.Name != "DrawText" && m.Name != "Refresh") continue;
                Console.WriteLine("  METHOD {0}", m.FullName);
                Disasm(m);
                Console.WriteLine();
            }
        }
    }
}
