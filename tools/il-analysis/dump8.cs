using System;
using Mono.Cecil;
using Mono.Cecil.Cil;
class Dump8 {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var t in asm.MainModule.GetTypes()) {
            if (t.FullName == "Microsoft.Xna.Framework.Content.ContentReader" && args.Length > 1) {
                Console.WriteLine("=== ContentReader declared methods ===");
                foreach (var m in t.Methods)
                    Console.WriteLine("  " + m.Name + " : " + m.ReturnType.Name + (m.IsVirtual ? " (virtual)" : ""));
                continue;
            }
            if (t.Name != "SavingInfoScene") continue;
            Console.WriteLine("=== {0} (base {1}) ===", t.FullName, t.BaseType);
            foreach (var f in t.Fields) Console.WriteLine("  FIELD {0} {1}", f.FieldType, f.Name);
            foreach (var m in t.Methods) {
                if (!m.HasBody) continue;
                bool interesting = false;
                foreach (var ins in m.Body.Instructions)
                    if (ins.OpCode == OpCodes.Ldstr) interesting = true;
                if (!interesting) continue;
                Console.WriteLine("  METHOD {0}", m.Name);
                foreach (var ins in m.Body.Instructions)
                    Console.WriteLine("    IL_{0:x4}: {1} {2}", ins.Offset, ins.OpCode, ins.Operand);
            }
        }
    }
}
