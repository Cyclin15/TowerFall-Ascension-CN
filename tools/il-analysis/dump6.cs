using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump6 {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            if (t.FullName != "Microsoft.Xna.Framework.Graphics.SpriteFont") continue;
            foreach (var m in t.Methods)
                Console.WriteLine(m.Name + (m.HasBody ? " (body " + m.Body.Instructions.Count + ")" : ""));
        }
    }
}
