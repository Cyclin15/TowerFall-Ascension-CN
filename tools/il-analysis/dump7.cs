using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump7 {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            if (t.FullName != "Microsoft.Xna.Framework.Graphics.SpriteFont") continue;
            foreach (var m in t.Methods) {
                if (m.Name != "InternalDraw" || !m.HasBody) continue;
                foreach (var ins in m.Body.Instructions)
                    Console.WriteLine("IL_{0:x4}: {1} {2}", ins.Offset, ins.OpCode, ins.Operand);
            }
        }
    }
}
