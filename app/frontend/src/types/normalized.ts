export interface NormalizedItem {
  id: string
  source: string
  source_label: string
  source_item_id: string
  title: string
  creators: string[]
  date_display: string | null
  object_type: string
  institution: string | null
  thumbnail_url: string | null
  record_url: string | null
  manifest_url: string | null
  has_iiif_manifest: boolean
  has_images: boolean
  has_ocr: boolean
  availability: string
  relevance_score: number
  normalization_warnings: string[]
}
