"""Static fixture records for Europeana connector fallback mode."""

FIXTURE_EUROPEANA_RECORDS: list[dict[str, object]] = [
    {
        "source_item_id": "/2021664/dante_ms_1",
        "title": "Dante manuscript fragment (Europeana)",
        "creators": ["Dante Alighieri"],
        "date_display": "14th century",
        "object_type": "manuscript",
        "institution": "Europeana partner institution",
        "record_url": "https://www.europeana.eu/en/item/2021664/dante_ms_1",
        "manifest_url": "https://iiif.europeana.eu/presentation/2021664/dante_ms_1/manifest",
        "thumbnail_url": "https://cdn.europeana.eu/thumbs/dante_ms_1.jpg",
    },
    {
        "source_item_id": "/2021664/book_of_hours_1",
        "title": "Book of Hours (Europeana)",
        "creators": ["Unknown"],
        "date_display": "15th century",
        "object_type": "manuscript",
        "institution": "Europeana partner institution",
        "record_url": "https://www.europeana.eu/en/item/2021664/book_of_hours_1",
        "manifest_url": "https://iiif.europeana.eu/presentation/2021664/book_of_hours_1/manifest",
        "thumbnail_url": "https://cdn.europeana.eu/thumbs/book_of_hours_1.jpg",
    },
]
