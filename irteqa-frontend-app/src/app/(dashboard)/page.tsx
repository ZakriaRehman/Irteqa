"use client"

import { useSessions } from "@/lib/hooks/use-sessions"
import { usePatients } from "@/lib/hooks/use-patients"
import { StatsCard } from "@/components/dashboard/stats-card"
import { SessionCard } from "@/components/sessions/session-card"
import { Button } from "@/components/ui/button"
import { Users, Calendar, FileText, Clock, Plus } from "lucide-react"
import Link from "next/link"

export default function DashboardPage() {
  const { data: sessions = [], isLoading: sessionsLoading } = useSessions()
  const { data: patients = [], isLoading: patientsLoading } = usePatients()

  // Calculate stats
  const todaySessions = sessions.filter((s) => {
    const today = new Date().toDateString()
    return new Date(s.start_at).toDateString() === today
  })

  const activeSessions = sessions.filter((s) => s.status === "in_progress")
  const completedToday = todaySessions.filter((s) => s.status === "completed")
  const upcomingSessions = sessions.filter((s) => s.status === "scheduled")

  const recentSessions = sessions.slice(0, 5)

  if (sessionsLoading || patientsLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-gray-500">Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Welcome back, Dr. Therapist</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatsCard
          title="Active Patients"
          value={patients.filter((p) => p.status === "active").length}
          icon={Users}
        />
        <StatsCard
          title="Today's Sessions"
          value={todaySessions.length}
          icon={Calendar}
        />
        <StatsCard
          title="Active Sessions"
          value={activeSessions.length}
          icon={Clock}
        />
        <StatsCard
          title="Completed Today"
          value={completedToday.length}
          icon={FileText}
        />
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="flex gap-4">
          <Link href="/sessions">
            <Button size="lg">
              <Calendar className="mr-2 h-5 w-5" />
              View All Sessions
            </Button>
          </Link>
          <Link href="/patients">
            <Button size="lg" variant="outline">
              <Users className="mr-2 h-5 w-5" />
              View Patients
            </Button>
          </Link>
        </div>
      </div>

      {/* Recent Sessions */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Recent Sessions</h2>
          <Link href="/sessions">
            <Button variant="ghost">View All</Button>
          </Link>
        </div>

        {recentSessions.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed">
            <Calendar className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No sessions yet
            </h3>
            <p className="text-gray-500 mb-4">
              Get started by creating your first session
            </p>
            <Link href="/sessions">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Session
              </Button>
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {recentSessions.map((session) => (
              <SessionCard key={session.id} session={session} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}