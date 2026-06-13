import { useState } from 'react'
import { useGateCenterStore } from '@/stores/gateCenterStore'
import BypassModal from './BypassModal'

interface BypassTriggerProps {
  gateId?: string
}

export default function BypassTrigger({ gateId }: BypassTriggerProps) {
  const role = typeof window !== 'undefined' ? localStorage.getItem('X-User-Role') : null
  const selectedGate = useGateCenterStore((state) => state.selectedGate)
  const applyBypass = useGateCenterStore((state) => state.applyBypass)
  const [isModalOpen, setIsModalOpen] = useState(false)

  if (role !== 'tech_lead') return null

  const handleBypass = () => {
    setIsModalOpen(true)
  }

  const canBypass =
    selectedGate?.status === 'pending' && (!gateId || selectedGate.gate_id === gateId)

  const handleSubmit = async (payload: {
    stage_id: string
    skill_id: string
    triggered_by: string
    reason: string
    authorizer_token: string
    deadline_hours: number
  }) => {
    if (!gateId) return
    await applyBypass(gateId, payload)
    setIsModalOpen(false)
  }

  return (
    <>
      <button
        onClick={handleBypass}
        disabled={!canBypass}
        className="px-4 py-2 rounded-md bg-orange-600 text-white text-sm hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        申请旁路
      </button>

      {isModalOpen && selectedGate && (
        <BypassModal
          gate={selectedGate}
          onClose={() => setIsModalOpen(false)}
          onSubmit={handleSubmit}
        />
      )}
    </>
  )
}
