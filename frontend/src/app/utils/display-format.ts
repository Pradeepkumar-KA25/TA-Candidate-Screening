export function sanitizeDisplayText(value: string | null | undefined): string {
  if (!value) {
    return '—';
  }

  const decoded = decodePotentiallyEncodedText(value.trim());
  const withoutTags = decoded.replace(/<[^>]*>/g, ' ');
  const normalized = withoutTags
    .replace(/script/gi, ' ')
    .replace(/[^a-zA-Z0-9.,()\-_'&/\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  return normalized || '—';
}

export function sanitizeEmailAddress(value: string | null | undefined): string {
  if (!value) {
    return '—';
  }

  const decoded = decodePotentiallyEncodedText(value.trim());
  const withoutTags = decoded.replace(/<[^>]*>/g, ' ');
  const normalized = withoutTags.replace(/script/gi, ' ').replace(/\s+/g, ' ').trim();

  return normalized || '—';
}

export function sanitizeCandidateName(value: string | null | undefined): string {
  const normalized = sanitizeDisplayText(value);
  if (normalized === '—') {
    return 'Unknown Candidate';
  }

  return normalized.slice(0, 80);
}

export function summarizeSkills(skills: string[] | null | undefined, maxItems: number = 3): string {
  if (!skills || skills.length === 0) {
    return '—';
  }

  const cleaned = skills.map((item) => sanitizeDisplayText(item)).filter((item) => item !== '—');
  if (cleaned.length === 0) {
    return '—';
  }

  if (cleaned.length <= maxItems) {
    return cleaned.join(', ');
  }

  return `${cleaned.slice(0, maxItems).join(', ')} +${cleaned.length - maxItems} more`;
}

function decodePotentiallyEncodedText(input: string): string {
  let current = input;

  for (let index = 0; index < 2; index += 1) {
    try {
      const decoded = decodeURIComponent(current);
      if (decoded === current) {
        break;
      }
      current = decoded;
    } catch {
      break;
    }
  }

  return current;
}
