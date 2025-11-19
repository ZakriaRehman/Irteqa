"use client"

import { useState } from "react"
import { usePatients } from "@/lib/hooks/use-patients"
import { useSessions } from "@/lib/hooks/use-sessions"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { getStatusColor } from "@/lib/utils"
import {
  Search,
  Filter,
  Calendar,
  Mail,
  Phone,
  FileText,
  Eye,
  Clock,
  CheckCircle,
  AlertCircle
} from "lucide-react"

interface Patient {
  id: string
  name: string
  email: string
  phone?: string
  status: string
  concerns?: string
  created_at: string
}

export default function PatientsPage() {
  const { data: patients = [], isLoading } = usePatients()
  const { data: sessions = [] } = useSessions()

  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null)

  // Filter patients based on search and status
  const filteredPatients = patients.filter((patient: Patient) => {
    const matchesSearch =
      patient.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      patient.email.toLowerCase().includes(searchQuery.toLowerCase())

    const matchesStatus = statusFilter === "all" || patient.status.toLowerCase() === statusFilter.toLowerCase()

    return matchesSearch && matchesStatus
  })

  // Get patient statistics
  const getPatientSessions = (patientId: string) => {
    return sessions.filter((s: any) => s.client_id === patientId)
  }

  const getLastSessionDate = (patientId: string) => {
    const patientSessions = getPatientSessions(patientId)
    if (patientSessions.length === 0) return null

    const sorted = patientSessions.sort((a: any, b: any) =>
      new Date(b.start_at).getTime() - new Date(a.start_at).getTime()
    )
    return new Date(sorted[0].start_at)
  }

  const getOnboardingProgress = (patient: Patient) => {
    if (patient.status.toLowerCase() !== 'onboarding') return null

    // Simple progress calculation - can be enhanced with actual data
    const hasPhone = !!patient.phone
    const hasConcerns = !!patient.concerns

    let progress = 25 // Base progress for being created
    if (hasPhone) progress += 25
    if (hasConcerns) progress += 25
    // Assume 25% for consents (would need actual consent data)

    return progress
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p>Loading patients...</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Patients</h1>
        <p className="text-gray-600">Manage your patient roster and track their progress</p>
      </div>

      {/* Stats Row */}
      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Patients</p>
              <p className="text-2xl font-bold">{patients.length}</p>
            </div>
            <FileText className="h-8 w-8 text-blue-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active</p>
              <p className="text-2xl font-bold text-green-600">
                {patients.filter((p: Patient) => p.status.toLowerCase() === 'active').length}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Onboarding</p>
              <p className="text-2xl font-bold text-yellow-600">
                {patients.filter((p: Patient) => p.status.toLowerCase() === 'onboarding').length}
              </p>
            </div>
            <Clock className="h-8 w-8 text-yellow-500" />
          </div>
        </Card>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Inactive</p>
              <p className="text-2xl font-bold text-gray-600">
                {patients.filter((p: Patient) => p.status.toLowerCase() === 'inactive').length}
              </p>
            </div>
            <AlertCircle className="h-8 w-8 text-gray-500" />
          </div>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search patients by name or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <Filter className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="onboarding">Onboarding</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Results Count */}
      <p className="text-sm text-gray-600 mb-4">
        Showing {filteredPatients.length} of {patients.length} patients
      </p>

      {/* Patients Grid */}
      <div className="grid gap-4">
        {filteredPatients.length === 0 ? (
          <Card className="p-12 text-center">
            <p className="text-gray-500">No patients found matching your criteria</p>
          </Card>
        ) : (
          filteredPatients.map((patient: Patient) => {
            const lastSession = getLastSessionDate(patient.id)
            const onboardingProgress = getOnboardingProgress(patient)
            const patientSessions = getPatientSessions(patient.id)

            return (
              <Card key={patient.id} className="p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                        <span className="text-lg font-semibold text-blue-600">
                          {patient.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold">{patient.name}</h3>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <span className="flex items-center gap-1">
                            <Mail className="h-3 w-3" />
                            {patient.email}
                          </span>
                          {patient.phone && (
                            <span className="flex items-center gap-1">
                              <Phone className="h-3 w-3" />
                              {patient.phone}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Patient Info */}
                    <div className="grid md:grid-cols-3 gap-4 mb-3">
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Status</p>
                        <Badge className={getStatusColor(patient.status)}>
                          {patient.status}
                        </Badge>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Total Sessions</p>
                        <p className="font-semibold">{patientSessions.length}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Last Session</p>
                        <p className="font-semibold">
                          {lastSession
                            ? lastSession.toLocaleDateString()
                            : 'No sessions yet'}
                        </p>
                      </div>
                    </div>

                    {/* Onboarding Progress */}
                    {onboardingProgress !== null && (
                      <div className="mb-3">
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-gray-600">Onboarding Progress</span>
                          <span className="font-semibold text-blue-600">{onboardingProgress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all"
                            style={{ width: `${onboardingProgress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Concerns */}
                    {patient.concerns && (
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs text-gray-500 mb-1">Presenting Concerns</p>
                        <p className="text-sm text-gray-700 line-clamp-2">{patient.concerns}</p>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-2 ml-4">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedPatient(patient)}
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl">
                        <DialogHeader>
                          <DialogTitle>{patient.name}</DialogTitle>
                          <DialogDescription>Patient Details</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                          <div>
                            <h4 className="font-semibold mb-2">Contact Information</h4>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-sm text-gray-600">Email</p>
                                <p>{patient.email}</p>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Phone</p>
                                <p>{patient.phone || 'Not provided'}</p>
                              </div>
                            </div>
                          </div>
                          <div>
                            <h4 className="font-semibold mb-2">Status & Timeline</h4>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-sm text-gray-600">Current Status</p>
                                <Badge className={getStatusColor(patient.status)}>
                                  {patient.status}
                                </Badge>
                              </div>
                              <div>
                                <p className="text-sm text-gray-600">Joined</p>
                                <p>{new Date(patient.created_at).toLocaleDateString()}</p>
                              </div>
                            </div>
                          </div>
                          <div>
                            <h4 className="font-semibold mb-2">Session History</h4>
                            <p className="text-sm text-gray-600">
                              Total Sessions: {patientSessions.length}
                            </p>
                            <p className="text-sm text-gray-600">
                              Last Session: {lastSession?.toLocaleDateString() || 'No sessions yet'}
                            </p>
                          </div>
                          {patient.concerns && (
                            <div>
                              <h4 className="font-semibold mb-2">Presenting Concerns</h4>
                              <p className="text-sm text-gray-700">{patient.concerns}</p>
                            </div>
                          )}
                        </div>
                      </DialogContent>
                    </Dialog>

                    <Button size="sm" variant="outline">
                      <Calendar className="h-4 w-4 mr-2" />
                      Schedule
                    </Button>
                  </div>
                </div>
              </Card>
            )
          })
        )}
      </div>
    </div>
  )
}
