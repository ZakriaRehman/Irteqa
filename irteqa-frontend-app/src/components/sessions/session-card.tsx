import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Session } from "@/types"
import { formatDateTime, getStatusColor } from "@/lib/utils"
import { PlayCircle } from "lucide-react"
import Link from "next/link"

interface SessionCardProps {
  session: Session
}

export function SessionCard({ session }: SessionCardProps) {
  return (
    <Card className="p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-lg font-semibold">
              {session.client_name || "Unknown Client"}
            </h3>
            <Badge className={getStatusColor(session.status)}>
              {session.status}
            </Badge>
          </div>
          <p className="text-sm text-gray-600">{session.client_email}</p>
          <p className="text-xs text-gray-400 mt-1">
            {formatDateTime(session.start_at)}
          </p>
        </div>
        <Link href={`/sessions/${session.id}/live`}>
          <Button size="lg" className="bg-green-600 hover:bg-green-700">
            <PlayCircle className="mr-2 h-5 w-5" />
            Start
          </Button>
        </Link>
      </div>
    </Card>
  )
}
