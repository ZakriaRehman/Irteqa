"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { CheckCircle2 } from "lucide-react";

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    concerns: "",
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [onboardingLink, setOnboardingLink] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/v1/inquiries", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Tenant-ID": "demo-tenant",
          "X-Idempotency-Key": `inquiry-${Date.now()}`,
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        // The backend returns the inquiry with client_id
        // We need to fetch the client to get the ID for onboarding
        const clientResponse = await fetch(`http://localhost:8000/v1/clients`, {
          headers: {
            "X-Tenant-ID": "demo-tenant",
          },
        });

        if (clientResponse.ok) {
          const clientsData = await clientResponse.json();
          // Find the client that matches the email we just submitted
          const client = clientsData.data.find((c: any) => c.email === formData.email);

          if (client) {
            const onboardingUrl = `/onboarding/${client.id}`;
            setOnboardingLink(onboardingUrl);
            setSubmitted(true);
          }
        }
      } else {
        alert("Failed to submit form. Please try again.");
      }
    } catch (error) {
      console.error("Error submitting form:", error);
      alert("An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <Card className="max-w-md w-full">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-4">
              <CheckCircle2 className="w-16 h-16 text-green-500" />
            </div>
            <CardTitle className="text-2xl">Thank You!</CardTitle>
            <CardDescription>
              We&apos;ve received your inquiry and sent a welcome email to {formData.email}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900 mb-2">
                <strong>Next Steps:</strong>
              </p>
              <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
                <li>Check your email for the welcome message</li>
                <li>Click the onboarding link to get started</li>
                <li>Complete your intake form</li>
                <li>Sign consent forms</li>
                <li>Get matched with a therapist</li>
              </ol>
            </div>

            <div className="pt-4">
              <p className="text-sm text-gray-600 mb-2">
                For testing purposes, you can start the onboarding process now:
              </p>
              <Button
                className="w-full"
                onClick={() => window.location.href = onboardingLink}
              >
                Start Onboarding (Demo)
              </Button>
            </div>

            <Button
              variant="outline"
              className="w-full"
              onClick={() => {
                setSubmitted(false);
                setFormData({ name: "", email: "", phone: "", concerns: "" });
              }}
            >
              Submit Another Inquiry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-2xl mx-auto py-12">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Irteqa Health
          </h1>
          <p className="text-lg text-gray-600">
            Professional Mental Health Services
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Get Started Today</CardTitle>
            <CardDescription>
              Fill out this form and we&apos;ll send you an email to begin your journey to better mental health.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name *</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="John Doe"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email Address *</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="john@example.com"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number</Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="(555) 123-4567"
                  value={formData.phone}
                  onChange={(e) =>
                    setFormData({ ...formData, phone: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="concerns">
                  Tell us about your concerns *
                </Label>
                <Textarea
                  id="concerns"
                  placeholder="I'm looking for help with anxiety and stress management..."
                  rows={5}
                  value={formData.concerns}
                  onChange={(e) =>
                    setFormData({ ...formData, concerns: e.target.value })
                  }
                  required
                />
              </div>

              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Submitting..." : "Submit Inquiry"}
              </Button>
            </form>

            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                <strong>What happens next?</strong>
              </p>
              <ul className="text-sm text-gray-600 mt-2 space-y-1">
                <li>• You&apos;ll receive a welcome email with an onboarding link</li>
                <li>• Complete a brief intake form (10-15 minutes)</li>
                <li>• Review and sign consent forms</li>
                <li>• Get matched with a licensed therapist</li>
                <li>• Schedule your first session</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        <div className="text-center mt-8 text-sm text-gray-500">
          <p>This is a demo environment for testing the onboarding workflow</p>
        </div>
      </div>
    </div>
  );
}
