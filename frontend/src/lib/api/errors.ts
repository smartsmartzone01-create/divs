import type { DIVSLanguage } from "@/components/preferences/preferences-provider";

type ErrorPayload = {
  code?: unknown;
  detail?: unknown;
  message?: unknown;
  success?: unknown;
};

const messages = {
  en: {
    badRequest: "Please check the information you entered and try again.",
    unauthorized: "Your session may have expired. Please sign in again.",
    forbidden: "You don't have permission to perform this action.",
    notFound: "We couldn't find the information you requested.",
    conflict: "This action conflicts with the current status. Refresh the page and try again.",
    tooLarge: "This file is too large. Please choose a smaller file.",
    rateLimited: "Too many attempts. Please wait a moment and try again.",
    unavailable: "The service is temporarily unavailable. Please try again shortly.",
    network: "We couldn't connect. Check your internet connection and try again.",
    unexpected: "We couldn't complete your request. Please try again. If the problem continues, contact DIVS support.",
    verificationFinal: "This verification has already received a final decision.",
    evidenceRejected: "This file could not be accepted. Please check the file and try again.",
  },
  sw: {
    badRequest: "Tafadhali kagua taarifa ulizoingiza kisha ujaribu tena.",
    unauthorized: "Huenda muda wa kipindi chako umeisha. Tafadhali ingia tena.",
    forbidden: "Huna ruhusa ya kufanya kitendo hiki.",
    notFound: "Hatukuweza kupata taarifa ulizoomba.",
    conflict: "Kitendo hiki hakiendani na hali ya sasa. Onyesha upya ukurasa kisha ujaribu tena.",
    tooLarge: "Faili hili ni kubwa mno. Tafadhali chagua faili dogo zaidi.",
    rateLimited: "Umejaribu mara nyingi mno. Subiri kidogo kisha ujaribu tena.",
    unavailable: "Huduma haipatikani kwa muda. Tafadhali jaribu tena baada ya muda mfupi.",
    network: "Imeshindikana kuunganisha. Kagua intaneti yako kisha ujaribu tena.",
    unexpected: "Imeshindikana kukamilisha ombi lako. Jaribu tena. Tatizo likiendelea, wasiliana na msaada wa DIVS.",
    verificationFinal: "Uhakiki huu tayari umepata uamuzi wa mwisho.",
    evidenceRejected: "Faili hili halikuweza kukubaliwa. Kagua faili kisha ujaribu tena.",
  },
} as const;

export function userMessageForStatus(status: number, language: DIVSLanguage): string {
  const copy = messages[language];
  if (status === 400 || status === 422) return copy.badRequest;
  if (status === 401) return copy.unauthorized;
  if (status === 403) return copy.forbidden;
  if (status === 404) return copy.notFound;
  if (status === 409) return copy.conflict;
  if (status === 413) return copy.tooLarge;
  if (status === 429) return copy.rateLimited;
  if ([502, 503, 504].includes(status)) return copy.unavailable;
  return copy.unexpected;
}

/** Translate API failures without exposing raw server messages or exception details. */
export function userMessageForError(error: unknown, language: DIVSLanguage): string {
  const copy = messages[language];
  if (error instanceof TypeError) return copy.network;

  if (typeof error === "object" && error !== null) {
    const candidate = error as { status?: unknown; payload?: unknown };
    const payload = candidate.payload as ErrorPayload | undefined;
    const code = typeof payload?.code === "string" ? payload.code : "";

    if (code === "VERIFICATION_ALREADY_FINAL") return copy.verificationFinal;
    if (code === "EVIDENCE_FILE_REJECTED") return copy.evidenceRejected;

    if (typeof candidate.status === "number") {
      return userMessageForStatus(candidate.status, language);
    }
  }

  return copy.unexpected;
}
