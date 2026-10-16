using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump2 {
    static void Disasm(MethodDefinition m) {
        if (!m.HasBody) { Console.WriteLine("    (no body)"); return; }
        foreach (var ins in m.Body.Instructions)
            Console.WriteLine("    IL_{0:x4}: {1} {2}", ins.Offset, ins.OpCode, ins.Operand);
    }
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            bool isCR = t.FullName == "Microsoft.Xna.Framework.Content.ContentReader";
            bool isList = t.FullName.StartsWith("Microsoft.Xna.Framework.Content.ListReader`1");
            bool isPrim = t.FullName == "Microsoft.Xna.Framework.Content.CharReader"
                       || t.FullName == "Microsoft.Xna.Framework.Content.RectangleReader"
                       || t.FullName == "Microsoft.Xna.Framework.Content.Vector3Reader"
                       || t.FullName == "Microsoft.Xna.Framework.Content.StringReader";
            if (!(isCR || isList || isPrim)) continue;
            Console.WriteLine("=== TYPE {0} (base {1}) ===", t.FullName, t.BaseType);
            foreach (var m in t.Methods) {
                if (m.Name == ".ctor" && isPrim) continue;
                if (!(m.Name == ".ctor" || m.Name == "Read" || m.Name == "ReadObject"
                   || m.Name == "Read7BitEncodedInt" || m.Name == "ReadAsset"
                   || m.Name == "ReadSharedResource" || m.Name == "ReadString")) continue;
                if (!m.HasBody) continue;
                Console.WriteLine("  METHOD {0}", m.FullName);
                Disasm(m);
            }
        }
    }
}
