export interface NormalizedItem {
  id: string
  source: string
  source_label: string
  source_item_id: string

  title: string
  subtitle: string | null
  creators: string[]
  date_display: string | null
  date_sort: string | null
  languages: string[]
  object_type: string
  description: string | null

  institution: string | null
  collection: string | null
  rights: string | null
  license: string | null

  thumbnail_url: string | null
  preview_image_url: string | null
  record_url: string | null
  manifest_url: string | null
  iiif_image_service_url: string | null

  has_iiif_manifest: boolean
  has_images: boolean
  has_ocr: boolean
  availability: string
  relevance_score: number
  normalization_warnings: string[]
}
