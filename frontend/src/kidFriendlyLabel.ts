import type { KidFriendly } from './api/recipes'

const labels: Record<KidFriendly, string> = {
  yes: 'yes',
  with_adjustments: 'with adjustments',
  no: 'no',
}

export function kidFriendlyLabel(value: KidFriendly): string {
  return labels[value]
}
