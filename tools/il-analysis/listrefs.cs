using System;
using Mono.Cecil;
class ListRefs {
    static void Main(string[] args) {
        var asm = AssemblyDefinition.ReadAssembly(args[0]);
        foreach (var r in asm.MainModule.AssemblyReferences)
            Console.WriteLine(r.Name + " v" + r.Version);
        Console.WriteLine("-- resources --");
        foreach (var res in asm.MainModule.Resources)
            Console.WriteLine(res.ResourceType + " " + res.Name);
    }
}
