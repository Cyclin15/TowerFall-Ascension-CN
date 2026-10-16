using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump4 {
    static void Disasm(MethodDefinition m) {
        foreach (var ins in m.Body.Instructions)
            Console.WriteLine("    IL_{0:x4}: {1} {2}", ins.Offset, ins.OpCode, ins.Operand);
    }
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            if (t.FullName != "Microsoft.Xna.Framework.Graphics.SpriteFont") continue;
            foreach (var m in t.Methods) {
                if (m.Name != "InternalMeasure" && m.Name != "DrawInto"
                 && m.Name != "InternalDrawString") continue;
                if (!m.HasBody) continue;
                Console.WriteLine("  METHOD {0}", m.FullName);
                Disasm(m);
                Console.WriteLine();
            }
        }
    }
}
