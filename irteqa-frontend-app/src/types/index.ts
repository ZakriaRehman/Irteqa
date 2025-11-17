// Patient Types
export interface Patient {
  id: string
  tenant_id: string
  status: "onboarding" | "active" | "inactive" | "terminated"
  name: string
  email: string
  phone?: string
  concerns?: string
  created_at: string
}

// Session Types
export interface Session {
  id: string
  tenant_id: string
  client_id: string
  therapist_id: string
  status: "scheduled" | "in_progress" | "completed" | "cancelled"
  start_at: string
  end_at?: string
  notes?: string
  transcript?: string
  soap_summary?: any
  live_assist_enabled?: boolean
  created_at: string
  client_name?: string
  client_email?: string
}

// Dashboard Stats
export interface DashboardStats {
  active_patients: number
  sessions_today: number
  sessions_this_week: number
  pending_notes: number
  upcoming_sessions: number
}

// Transcript
export interface TranscriptSegment {
  text: string
  is_final: boolean
  speaker?: number
  timestamp: number
}

// API Response
export interface StartSessionResponse {
  live_assist: boolean
  rt?: {
    token: string
    ws_audio_url: string
    session_id: string
  }
}