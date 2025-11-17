"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Checkbox } from "@/components/ui/checkbox";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";

type Step = "intake" | "consents" | "complete";

interface Consent {
  type: string;
  title: string;
  description: string;
  required: boolean;
  signed: boolean;
  consent_id?: string;
}

export default function OnboardingPage() {
  const params = useParams();
  const router = useRouter();
  const clientId = params.clientId as string;

  const [currentStep, setCurrentStep] = useState<Step>("intake");
  const [loading, setLoading] = useState(false);

  // Intake form state
  const [intakeData, setIntakeData] = useState({
    date_of_birth: "",
    presenting_concerns: "",
    previous_therapy: "",
    medications: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
    insurance_provider: "",
    insurance_member_id: "",
    preferred_session_type: "video",
    goals: "",
  });

  // Consents state
  const [consents, setConsents] = useState<Consent[]>([]);
  const [agreedConsents, setAgreedConsents] = useState<Set<string>>(new Set());

  const steps = [
    { id: "intake", label: "Intake Form" },
    { id: "consents", label: "Consent Forms" },
    { id: "complete", label: "Complete" },
  ];

  const currentStepIndex = steps.findIndex((s) => s.id === currentStep);
  const progress = ((currentStepIndex + 1) / steps.length) * 100;

  useEffect(() => {
    // Load consents when on consent step
    if (currentStep === "consents") {
      loadConsents();
    }
  }, [currentStep]);

  const loadConsents = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/v1/intake/${clientId}/consents`,
        {
          headers: {
            "X-Tenant-ID": "demo-tenant",
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setConsents(data.consents || []);
      }
    } catch (error) {
      console.error("Error loading consents:", error);
    }
  };

  const handleIntakeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(
        `http://localhost:8000/v1/intake/${clientId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Tenant-ID": "demo-tenant",
          },
          body: JSON.stringify(intakeData),
        }
      );

      if (response.ok) {
        setCurrentStep("consents");
      } else {
        alert("Failed to submit intake form");
      }
    } catch (error) {
      console.error("Error submitting intake:", error);
      alert("An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleConsentToggle = (consentType: string) => {
    const newAgreed = new Set(agreedConsents);
    if (newAgreed.has(consentType)) {
      newAgreed.delete(consentType);
    } else {
      newAgreed.add(consentType);
    }
    setAgreedConsents(newAgreed);
  };

  const handleConsentsSubmit = async () => {
    setLoading(true);

    try {
      // Sign each agreed consent
      for (const consentType of agreedConsents) {
        await fetch(
          `http://localhost:8000/v1/intake/${clientId}/consents/${consentType}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-Tenant-ID": "demo-tenant",
            },
            body: JSON.stringify({}),
          }
        );
      }

      // Complete onboarding
      const response = await fetch(
        `http://localhost:8000/v1/intake/${clientId}/complete`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Tenant-ID": "demo-tenant",
          },
        }
      );

      if (response.ok) {
        setCurrentStep("complete");
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to complete onboarding");
      }
    } catch (error) {
      console.error("Error submitting consents:", error);
      alert("An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const requiredConsents = consents.filter((c) => c.required);
  const allRequiredSigned = requiredConsents.every((c) =>
    agreedConsents.has(c.type)
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-3xl mx-auto py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to Irteqa Health
          </h1>
          <p className="text-gray-600">Let&apos;s get you started</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <Progress value={progress} className="h-2" />
          <div className="flex justify-between mt-4">
            {steps.map((step, index) => (
              <div
                key={step.id}
                className="flex items-center gap-2 text-sm"
              >
                {index < currentStepIndex ? (
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                ) : index === currentStepIndex ? (
                  <Circle className="w-5 h-5 text-blue-500 fill-blue-500" />
                ) : (
                  <Circle className="w-5 h-5 text-gray-300" />
                )}
                <span
                  className={
                    index <= currentStepIndex
                      ? "text-gray-900 font-medium"
                      : "text-gray-400"
                  }
                >
                  {step.label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        {currentStep === "intake" && (
          <Card>
            <CardHeader>
              <CardTitle>Intake Form</CardTitle>
              <CardDescription>
                Please provide some basic information to help us match you with
                the right therapist
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleIntakeSubmit} className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="dob">Date of Birth *</Label>
                    <Input
                      id="dob"
                      type="date"
                      value={intakeData.date_of_birth}
                      onChange={(e) =>
                        setIntakeData({
                          ...intakeData,
                          date_of_birth: e.target.value,
                        })
                      }
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="session-type">Preferred Session Type *</Label>
                    <select
                      id="session-type"
                      className="w-full h-10 px-3 rounded-md border border-input bg-background"
                      value={intakeData.preferred_session_type}
                      onChange={(e) =>
                        setIntakeData({
                          ...intakeData,
                          preferred_session_type: e.target.value,
                        })
                      }
                      required
                    >
                      <option value="video">Video Call</option>
                      <option value="phone">Phone Call</option>
                      <option value="in-person">In-Person</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="concerns">Presenting Concerns *</Label>
                  <Textarea
                    id="concerns"
                    placeholder="What brings you to therapy? What would you like to work on?"
                    rows={4}
                    value={intakeData.presenting_concerns}
                    onChange={(e) =>
                      setIntakeData({
                        ...intakeData,
                        presenting_concerns: e.target.value,
                      })
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="goals">Goals for Therapy *</Label>
                  <Textarea
                    id="goals"
                    placeholder="What are your goals for therapy?"
                    rows={3}
                    value={intakeData.goals}
                    onChange={(e) =>
                      setIntakeData({ ...intakeData, goals: e.target.value })
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="previous">Previous Therapy Experience</Label>
                  <Textarea
                    id="previous"
                    placeholder="Have you been in therapy before? If yes, please describe."
                    rows={3}
                    value={intakeData.previous_therapy}
                    onChange={(e) =>
                      setIntakeData({
                        ...intakeData,
                        previous_therapy: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="medications">Current Medications</Label>
                  <Input
                    id="medications"
                    placeholder="List any medications you're currently taking"
                    value={intakeData.medications}
                    onChange={(e) =>
                      setIntakeData({
                        ...intakeData,
                        medications: e.target.value,
                      })
                    }
                  />
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="emergency-name">Emergency Contact Name *</Label>
                    <Input
                      id="emergency-name"
                      placeholder="Full name"
                      value={intakeData.emergency_contact_name}
                      onChange={(e) =>
                        setIntakeData({
                          ...intakeData,
                          emergency_contact_name: e.target.value,
                        })
                      }
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="emergency-phone">Emergency Contact Phone *</Label>
                    <Input
                      id="emergency-phone"
                      type="tel"
                      placeholder="(555) 123-4567"
                      value={intakeData.emergency_contact_phone}
                      onChange={(e) =>
                        setIntakeData({
                          ...intakeData,
                          emergency_contact_phone: e.target.value,
                        })
                      }
                      required
                    />
                  </div>
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="insurance">Insurance Provider</Label>
                    <Input
                      id="insurance"
                      placeholder="e.g., Blue Cross Blue Shield"
                      value={intakeData.insurance_provider}
                      onChange={(e) =>
                        setIntakeData({
                          ...intakeData,
                          insurance_provider: e.target.value,
                        })
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="member-id">Member ID</Label>
                    <Input
                      id="member-id"
                      placeholder="Insurance member ID"
                      value={intakeData.insurance_member_id}
                      onChange={(e) =>
                        setIntakeData({
                          ...intakeData,
                          insurance_member_id: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>

                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    "Continue to Consent Forms"
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {currentStep === "consents" && (
          <Card>
            <CardHeader>
              <CardTitle>Consent Forms</CardTitle>
              <CardDescription>
                Please review and agree to the following consent forms
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {consents.map((consent) => (
                <div
                  key={consent.type}
                  className="border rounded-lg p-4 space-y-2"
                >
                  <div className="flex items-start gap-3">
                    <Checkbox
                      id={consent.type}
                      checked={agreedConsents.has(consent.type)}
                      onCheckedChange={() => handleConsentToggle(consent.type)}
                    />
                    <div className="flex-1">
                      <Label
                        htmlFor={consent.type}
                        className="text-base font-semibold cursor-pointer"
                      >
                        {consent.title}
                        {consent.required && (
                          <span className="text-red-500 ml-1">*</span>
                        )}
                      </Label>
                      <p className="text-sm text-gray-600 mt-1">
                        {consent.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}

              <div className="pt-4">
                <Button
                  className="w-full"
                  onClick={handleConsentsSubmit}
                  disabled={!allRequiredSigned || loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Completing...
                    </>
                  ) : (
                    "Complete Onboarding"
                  )}
                </Button>
                {!allRequiredSigned && (
                  <p className="text-sm text-red-600 mt-2 text-center">
                    Please agree to all required consent forms to continue
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {currentStep === "complete" && (
          <Card>
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                <CheckCircle2 className="w-20 h-20 text-green-500" />
              </div>
              <CardTitle className="text-2xl">Welcome Aboard!</CardTitle>
              <CardDescription>
                Your onboarding is complete. You&apos;re now an active patient.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="font-semibold text-green-900 mb-2">
                  What&apos;s Next?
                </p>
                <ol className="text-sm text-green-800 space-y-2 list-decimal list-inside">
                  <li>You&apos;ll be matched with a licensed therapist within 24 hours</li>
                  <li>You&apos;ll receive an email with therapist information</li>
                  <li>You can schedule your first session</li>
                  <li>Sessions are available via video, phone, or in-person</li>
                </ol>
              </div>

              <Button
                className="w-full"
                onClick={() => router.push("/")}
              >
                Go to Dashboard
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
