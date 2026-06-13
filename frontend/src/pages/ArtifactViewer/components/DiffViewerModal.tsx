import { useState, useMemo } from 'react'

export interface DiffLine {
  type: 'unchanged' | 'added' | 'removed' | 'modified'
  oldLine?: string
  newLine?: string
  oldLineNo?: number
  newLineNo?: number
}

function computeLCSMatrix(a: string[], b: string[]): number[][] {
  const dp: number[][] = Array(a.length + 1)
    .fill(0)
    .map(() => Array(b.length + 1).fill(0))
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      if (a[i - 1] === b[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1])
      }
    }
  }
  return dp
}

function backtrackDiff(a: string[], b: string[], dp: number[][]): DiffLine[] {
  const result: DiffLine[] = []
  let i = a.length
  let j = b.length
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && a[i - 1] === b[j - 1]) {
      result.unshift({
        type: 'unchanged',
        oldLine: a[i - 1],
        newLine: b[j - 1],
        oldLineNo: i,
        newLineNo: j,
      })
      i--
      j--
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      result.unshift({
        type: 'added',
        newLine: b[j - 1],
        newLineNo: j,
      })
      j--
    } else {
      result.unshift({
        type: 'removed',
        oldLine: a[i - 1],
        oldLineNo: i,
      })
      i--
    }
  }
  return result
}

function postProcessModified(diff: DiffLine[]): DiffLine[] {
  const result: DiffLine[] = []
  let idx = 0
  while (idx < diff.length) {
    if (diff[idx].type === 'removed') {
      const removedGroup: DiffLine[] = []
      while (idx < diff.length && diff[idx].type === 'removed') {
        removedGroup.push(diff[idx])
        idx++
      }
      const addedGroup: DiffLine[] = []
      while (idx < diff.length && diff[idx].type === 'added') {
        addedGroup.push(diff[idx])
        idx++
      }
      if (removedGroup.length === addedGroup.length && removedGroup.length > 0) {
        for (let k = 0; k < removedGroup.length; k++) {
          result.push({
            type: 'modified',
            oldLine: removedGroup[k].oldLine,
            newLine: addedGroup[k].newLine,
            oldLineNo: removedGroup[k].oldLineNo,
            newLineNo: addedGroup[k].newLineNo,
          })
        }
      } else {
        result.push(...removedGroup, ...addedGroup)
      }
    } else {
      result.push(diff[idx])
      idx++
    }
  }
  return result
}

function computeDiff(oldText: string, newText: string): DiffLine[] {
  const oldLines = oldText.split('\n')
  const newLines = newText.split('\n')
  const dp = computeLCSMatrix(oldLines, newLines)
  const diff = backtrackDiff(oldLines, newLines, dp)
  return postProcessModified(diff)
}

interface DiffViewerModalProps {
  oldContent: string
  newContent: string
  oldVersion: number
  newVersion: number
  onClose: () => void
}

export default function DiffViewerModal({
  oldContent,
  newContent,
  oldVersion,
  newVersion,
  onClose,
}: DiffViewerModalProps) {
  const [mode, setMode] = useState<'side-by-side' | 'inline'>('side-by-side')
  const diff = useMemo(() => computeDiff(oldContent, newContent), [oldContent, newContent])

  const typeStyle: Record<DiffLine['type'], string> = {
    unchanged: 'bg-white',
    added: 'bg-green-50',
    removed: 'bg-red-50',
    modified: 'bg-yellow-50',
  }

  const typePrefix: Record<DiffLine['type'], string> = {
    unchanged: '  ',
    added: '+ ',
    removed: '- ',
    modified: '~ ',
  }

  const typeBorder: Record<DiffLine['type'], string> = {
    unchanged: 'border-l-4 border-transparent',
    added: 'border-l-4 border-green-400',
    removed: 'border-l-4 border-red-400',
    modified: 'border-l-4 border-yellow-400',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <h3 className="font-semibold text-gray-800">
            版本对比: v{oldVersion} → v{newVersion}
          </h3>
          <div className="flex items-center gap-2">
            <div className="flex rounded border border-gray-300 overflow-hidden text-xs">
              <button
                onClick={() => setMode('side-by-side')}
                className={`px-3 py-1 ${mode === 'side-by-side' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
              >
                并排
              </button>
              <button
                onClick={() => setMode('inline')}
                className={`px-3 py-1 ${mode === 'inline' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}`}
              >
                行内
              </button>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-lg leading-none"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 px-4 py-2 border-b border-gray-200 text-xs bg-gray-50">
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-100 border border-green-400 inline-block" /> 新增</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-100 border border-red-400 inline-block" /> 删除</span>
          <span className="flex items-center gap-1"><span className="w-3 h-3 bg-yellow-100 border border-yellow-400 inline-block" /> 修改</span>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto">
          {mode === 'side-by-side' ? (
            <div className="flex min-h-full">
              {/* Old */}
              <div className="w-1/2 border-r border-gray-200">
                <div className="sticky top-0 bg-gray-100 text-xs px-3 py-1 text-gray-500 border-b border-gray-200 z-10">
                  v{oldVersion} (旧)
                </div>
                <div className="font-mono text-sm">
                  {diff.map((line, idx) => (
                    <div
                      key={`old-${idx}`}
                      className={`px-3 py-0.5 whitespace-pre ${typeStyle[line.type]} ${typeBorder[line.type]} ${line.type === 'added' ? 'opacity-30' : ''}`}
                    >
                      {line.type !== 'added' ? (
                        <>
                          <span className="text-gray-400 select-none w-8 inline-block text-right mr-2">
                            {line.oldLineNo ?? ''}
                          </span>
                          <span className="text-gray-500 select-none mr-1">{typePrefix[line.type]}</span>
                          {line.oldLine ?? ''}
                        </>
                      ) : (
                        <span className="text-gray-300 select-none">&nbsp;</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
              {/* New */}
              <div className="w-1/2">
                <div className="sticky top-0 bg-gray-100 text-xs px-3 py-1 text-gray-500 border-b border-gray-200 z-10">
                  v{newVersion} (新)
                </div>
                <div className="font-mono text-sm">
                  {diff.map((line, idx) => (
                    <div
                      key={`new-${idx}`}
                      className={`px-3 py-0.5 whitespace-pre ${typeStyle[line.type]} ${typeBorder[line.type]} ${line.type === 'removed' ? 'opacity-30' : ''}`}
                    >
                      {line.type !== 'removed' ? (
                        <>
                          <span className="text-gray-400 select-none w-8 inline-block text-right mr-2">
                            {line.newLineNo ?? ''}
                          </span>
                          <span className="text-gray-500 select-none mr-1">{typePrefix[line.type]}</span>
                          {line.newLine ?? ''}
                        </>
                      ) : (
                        <span className="text-gray-300 select-none">&nbsp;</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="font-mono text-sm">
              {diff.map((line, idx) => (
                <div
                  key={idx}
                  className={`px-3 py-0.5 whitespace-pre ${typeStyle[line.type]} ${typeBorder[line.type]}`}
                >
                  <span className="text-gray-400 select-none w-8 inline-block text-right mr-2">
                    {line.oldLineNo ?? line.newLineNo ?? ''}
                  </span>
                  <span className="text-gray-500 select-none mr-1">{typePrefix[line.type]}</span>
                  {line.type === 'modified' ? (
                    <span>
                      <span className="line-through text-red-600 mr-2">{line.oldLine}</span>
                      <span className="text-green-600">{line.newLine}</span>
                    </span>
                  ) : (
                    <span>{line.oldLine ?? line.newLine ?? ''}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
