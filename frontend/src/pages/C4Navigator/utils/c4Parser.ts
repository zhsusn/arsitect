export interface C4NodeInfo {
  id: string
  name: string
  type: 'Person' | 'System' | 'Container' | 'Component' | 'Boundary' | 'unknown'
  description?: string
  tech?: string[]
  filePath?: string
  interfaces?: string[]
}

export function parseC4Nodes(dslText: string): C4NodeInfo[] {
  const nodes: C4NodeInfo[] = []
  const metaMap: Record<string, Partial<C4NodeInfo>> = {}
  const lines = dslText.split('\n')

  // Parse metadata comments: %% @meta nodeId {"key":"value"}
  const metaRegex = /%%\s*@meta\s+(\w+)\s+(.+)/
  for (const line of lines) {
    const match = metaRegex.exec(line)
    if (match) {
      try {
        const [, nodeId, jsonStr] = match
        const data = JSON.parse(jsonStr)
        metaMap[nodeId] = data
      } catch {
        // ignore invalid meta
      }
    }
  }

  // Parse C4-style definitions: Type(id, "Name", "Desc", "Tech")
  const c4Regex =
    /^(Person|System|Container|Component|System_Boundary|Container_Boundary|Enterprise_Boundary)\s*\(\s*(\w+)\s*(?:,\s*"([^"]*)")?(?:,\s*"([^"]*)")?(?:,\s*"([^"]*)")?\s*\)/

  // Parse simple mermaid: id["Label"] or id[Label] or id(Label) or id{(Label)}
  const simpleRegex =
    /^(\w+)\s*(?:\[\s*"([^"]*)"\s*\]|\[\s*([^\]]+)\s*\]|\(\s*"([^"]*)"\s*\)|\(\s*([^)]+)\s*\)|\{\s*"([^"]*)"\s*\}|\{\s*([^}]+)\s*\})/

  for (const line of lines) {
    const stripped = line.trim()
    if (!stripped || stripped.startsWith('%%')) continue

    const c4Match = c4Regex.exec(stripped)
    if (c4Match) {
      const [, rawType, id, name, description, tech] = c4Match
      const type = rawType.includes('Boundary') ? 'Boundary' : rawType.toLowerCase()
      nodes.push({
        id,
        name: name || id,
        type: type as C4NodeInfo['type'],
        description,
        tech: tech ? [tech] : undefined,
        ...metaMap[id],
      })
      continue
    }

    const simpleMatch = simpleRegex.exec(stripped)
    if (simpleMatch) {
      const [, id, ...labels] = simpleMatch
      const name = labels.find((l) => l !== undefined) || id
      nodes.push({
        id,
        name: name.trim(),
        type: 'unknown',
        ...metaMap[id],
      })
    }
  }

  return nodes
}

export function findNodeById(dslText: string, nodeId: string): C4NodeInfo | null {
  const nodes = parseC4Nodes(dslText)
  return nodes.find((n) => n.id === nodeId) || null
}
