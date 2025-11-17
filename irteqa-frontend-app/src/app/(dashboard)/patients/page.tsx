"use client"

import { usePatients } from "@/lib/hooks/use-patients"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { getStatusColor } from "@/lib/utils"

export default function PatientsPage() {
  const { data: patients = [], isLoading } = usePatients()

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p>Loading patients...</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Patients</h1>
      <div className="grid gap-4">
        {patients.map((patient) => (
          <Card key={patient.id} className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">{patient.name}</h3>
                <p className="text-sm text-gray-600">{patient.email}</p>
              </div>
              <Badge className={getStatusColor(patient.status)}>
                {patient.status}
              </Badge>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}