# 📘 Phoenix Database Schema

## 🧩 Table: `Address`
> Stores geographic locations, including historical and modern addresses. Used across residence, business, and event records.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `address_id` | INTEGER | No | Yes |  |
| `address` | TEXT | No | No |  |
| `lat` | REAL | No | No |  |
| `long` | REAL | No | No |  |
| `old_address` | TEXT | No | No |  |
| `parent_address_id` | INTEGER | No | No |  |
| `parcel_id` | TEXT | No | No |  |
| `geometry` | TEXT | No | No |  |
| `start_date` | TEXT | No | No |  |
| `start_date_precision` | TEXT | No | No |  |
| `end_date` | TEXT | No | No |  |
| `end_date_precision` | TEXT | No | No |  |

## 🧩 Table: `BaptistCemetery`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `death_date` | TEXT | No | No |  |
| `first_name` | TEXT | No | No |  |
| `middle_name` | TEXT | No | No |  |
| `last_name` | TEXT | No | No |  |
| `buried_notes` | TEXT | No | No |  |
| `buried_location` | TEXT | No | No |  |
| `death_cause` | TEXT | No | No |  |

## 🧩 Table: `Biz`
> Main registry of businesses. Includes name, category, and relevant descriptive and temporal metadata.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `biz_id` | INTEGER | No | Yes |  |
| `biz_name` | TEXT | No | No |  |
| `start_date` | DATE | No | No |  |
| `start_date_precision` | TEXT | No | No |  |
| `end_date` | DATE | No | No |  |
| `end_date_precision` | TEXT | No | No |  |
| `description` | TEXT | No | No |  |
| `category` | TEXT | No | No |  |
| `address_id` | INTEGER | No | No |  |
| `map_link` | TEXT | No | No |  |
| `image_path` | TEXT | No | No |  |
| `external_url` | TEXT | No | No |  |
| `source_id` | INTEGER | No | No |  |
| `aliases` | TEXT | No | No |  |

## 🧩 Table: `BizEmployment`
> Links people to businesses where they were employed. Captures job title, dates, and optional notes.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `biz_id` | INTEGER | Yes | No |  |
| `person_id` | INTEGER | Yes | No |  |
| `start_date` | DATE | No | No |  |
| `start_date_precision` | TEXT | No | No |  |
| `end_date` | DATE | No | No |  |
| `end_date_precision` | TEXT | No | No |  |
| `job_title` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |
| `url` | TEXT | No | No |  |

## 🧩 Table: `BizEvents`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `event_id` | INTEGER | No | Yes |  |
| `biz_id` | INTEGER | Yes | No |  |
| `event_type` | TEXT | Yes | No |  |
| `event_start_date` | TEXT | No | No |  |
| `event_start_date_precision` | TEXT | No | No |  |
| `event_end_date` | TEXT | No | No |  |
| `event_end_date_precision` | TEXT | No | No |  |
| `person_id` | INTEGER | No | No |  |
| `description` | TEXT | No | No |  |
| `link_url` | TEXT | No | No |  |
| `source_id` | INTEGER | No | No |  |
| `created_at` | TIMESTAMP | No | No | CURRENT_TIMESTAMP |
| `summary` | TEXT | No | No |  |
| `original_text` | TEXT | No | No |  |

## 🧩 Table: `BizHistory`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `biz_id` | INTEGER | No | Yes |  |
| `owner_id` | INTEGER | No | Yes |  |
| `start_date` | DATE | No | Yes |  |
| `end_date` | DATE | No | No |  |
| `end_date_precision` | TEXT | No | No |  |
| `start_date_precision` | TEXT | No | No |  |

## 🧩 Table: `BizLineage`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `lineage_id` | INTEGER | No | Yes |  |
| `parent_biz_id` | INTEGER | No | No |  |
| `child_biz_id` | INTEGER | No | No |  |
| `relationship_type` | TEXT | No | No |  |

## 🧩 Table: `BizLocHistory`
> Tracks the address history of a business over time, including dates and additional notes.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `biz_id` | INTEGER | No | Yes |  |
| `address_id` | INTEGER | No | Yes |  |
| `start_date` | DATE | No | Yes |  |
| `start_date_precision` | TEXT | No | No |  |
| `end_date` | DATE | No | No |  |
| `end_date_precision` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |
| `url` | TEXT | No | No |  |

## 🧩 Table: `BizOwnership`
> Associates people with businesses they owned. Captures ownership role, title, duration, and notes.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `biz_ownership_id` | INTEGER | No | Yes |  |
| `biz_id` | INTEGER | No | No |  |
| `person_id` | INTEGER | No | No |  |
| `ownership_type` | TEXT | No | No |  |
| `title` | TEXT | No | No |  |
| `start_date` | TEXT | No | No |  |
| `start_date_precision` | TEXT | No | No |  |
| `end_date` | TEXT | No | No |  |
| `end_date_precision` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |

## 🧩 Table: `BizRoles`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `role_id` | INTEGER | No | Yes |  |
| `role_name` | TEXT | Yes | No |  |
| `description` | TEXT | No | No |  |

## 🧩 Table: `BusinessEvents`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `event_id` | INTEGER | No | Yes |  |
| `biz_id` | INTEGER | Yes | No |  |
| `event_type` | TEXT | Yes | No |  |
| `event_start_date` | TEXT | No | No |  |
| `event_start_date_precision` | TEXT | No | No |  |
| `event_end_date` | TEXT | No | No |  |
| `event_end_date_precision` | TEXT | No | No |  |
| `person_id` | INTEGER | No | No |  |
| `description` | TEXT | No | No |  |
| `link_url` | TEXT | No | No |  |
| `source_id` | INTEGER | No | No |  |
| `created_at` | TIMESTAMP | No | No | CURRENT_TIMESTAMP |
| `summary` | TEXT | No | No |  |
| `original_text` | TEXT | No | No |  |

## 🧩 Table: `Census`
> Captures census record information per person for a given year and residence.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `person_id` | INTEGER | No | No |  |
| `residence_id` | INTEGER | No | No |  |
| `census_year` | INTEGER | No | No |  |
| `person_age` | TEXT | No | No |  |
| `person_occupation` | TEXT | No | No |  |
| `census_housenumber` | INTEGER | No | No |  |
| `real_estate_value` | TEXT | No | No |  |
| `estate_value` | TEXT | No | No |  |
| `sex` | TEXT | No | No |  |
| `race` | TEXT | No | No |  |
| `married_this_year` | TEXT | No | No |  |
| `relation_to_head` | TEXT | No | No |  |
| `attended_school` | TEXT | No | No |  |
| `city` | TEXT | No | No |  |
| `state` | TEXT | No | No |  |
| `birth_place` | TEXT | No | No |  |
| `father_birth_place` | TEXT | No | No |  |
| `mother_birth_place` | TEXT | No | No |  |
| `native_language` | TEXT | No | No |  |
| `years_married` | INTEGER | No | No |  |
| `number_of_children_born` | INTEGER | No | No |  |
| `number_of_children_living` | INTEGER | No | No |  |
| `farm_owner` | TEXT | No | No |  |
| `rented_home_or_farm` | TEXT | No | No |  |
| `township_id` | INTEGER | No | No |  |
| `res_group_id` | INTEGER | No | No |  |
| `census_dwellnum` | INTEGER | No | No |  |
| `census_householdnum` | INTEGER | No | No |  |
| `disability_condition` |  | No | No | "" |
| `cannot_read_write` |  | No | No | "" |

## 🧩 Table: `CitationFieldMapping`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `citation_id` | INTEGER | No | No |  |
| `person_id` | INTEGER | No | No |  |
| `field_name` | TEXT | No | No |  |

## 🧩 Table: `Citations`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `source_id` | INTEGER | No | No |  |
| `detail` | TEXT | No | No |  |
| `citation_date` | TEXT | No | No |  |
| `transcription` | TEXT | No | No |  |
| `other_info` | TEXT | No | No |  |
| `web_address` | TEXT | No | No |  |

## 🧩 Table: `CustomLists`
> Stores customizable dropdown values for category fields across the app (e.g., org types, roles).

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `list_name` | TEXT | No | Yes |  |
| `list_values` | TEXT | No | No |  |

## 🧩 Table: `DeedParties`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `deed_party_id` | INTEGER | No | Yes |  |
| `deed_id` | INTEGER | No | No |  |
| `person_id` | INTEGER | No | No |  |
| `party_role` | TEXT | No | No |  |
| `party_order` | INTEGER | No | No |  |
| `ownership_type` | TEXT | No | No |  |

## 🧩 Table: `DeedPropertyLink`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `link_id` | INTEGER | No | Yes |  |
| `deed_id` | INTEGER | No | No |  |
| `property_id` | INTEGER | No | No |  |
| `address_id` | INTEGER | No | No |  |
| `relationship_type` | TEXT | No | No |  |
| `location_description` | TEXT | No | No |  |
| `valid_from` | TEXT | No | No |  |
| `valid_until` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |

## 🧩 Table: `DeedSources`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `source_id` | INTEGER | No | Yes |  |
| `source_name` | TEXT | No | No |  |
| `source_type` | TEXT | No | No |  |
| `source_location` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |

## 🧩 Table: `DeedTypes`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `type_id` | INTEGER | No | Yes |  |
| `type_name` | TEXT | No | No |  |
| `description` | TEXT | No | No |  |

## 🧩 Table: `Deeds`
> Stores land ownership transfer records, including grantor/grantee relationships, legal description, and source link.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `deed_id` | INTEGER | No | Yes |  |
| `deed_number` | TEXT | No | No |  |
| `book_number` | TEXT | No | No |  |
| `page_number` | TEXT | No | No |  |
| `recording_date` | TEXT | No | No |  |
| `execution_date` | TEXT | No | No |  |
| `deed_type` | TEXT | No | No |  |
| `consideration_amount` | REAL | No | No |  |
| `property_description` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |
| `created_at` | TIMESTAMP | No | No | CURRENT_TIMESTAMP |
| `deed_source` | TEXT | No | No |  |
| `acknowledge_date` | TEXT | No | No |  |
| `township_id` | INTEGER | No | No |  |
| `legal_text` | TEXT | No | No |  |

## 🧩 Table: `Doc`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `doc_id` | INTEGER | No | Yes |  |
| `doc_type_id` | INTEGER | No | No |  |
| `doc_title` | TEXT | No | No |  |
| `doc_description` | TEXT | No | No |  |
| `doc_path` | TEXT | No | No |  |
| `doc_link` | TEXT | No | No |  |
| `person_id` | INTEGER | No | No |  |

## 🧩 Table: `DocType`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `doc_id` | INTEGER | No | Yes |  |
| `doc_type_id` | INTEGER | No | No |  |
| `doc_type_name` | TEXT | No | No |  |
| `doc_title` | TEXT | No | No |  |
| `doc_description` | TEXT | No | No |  |
| `doc_path` | TEXT | No | No |  |
| `doc_link` | TEXT | No | No |  |

## 🧩 Table: `Education`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `person_id` | INTEGER | No | No |  |
| `school_name` | TEXT | No | No |  |
| `school_location` | TEXT | No | No |  |
| `level` | TEXT | No | No |  |
| `record_year` | INTEGER | No | No |  |
| `degree` | TEXT | No | No |  |
| `field_of_study` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |
| `position` | TEXT | No | No |  |

## 🧩 Table: `EventAddresses`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `event_id` | INTEGER | No | No |  |
| `address_id` | INTEGER | No | No |  |
| `label` | TEXT | No | No |  |

## 🧩 Table: `EventAttributes`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `event_id` | INTEGER | No | No |  |
| `attribute_name` | TEXT | No | No |  |
| `attribute_value` | TEXT | No | No |  |

## 🧩 Table: `EventBusinesses`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `event_id` | INTEGER | No | No |  |
| `biz_id` | INTEGER | No | No |  |
| `role` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |

## 🧩 Table: `EventMedia`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `media_id` | INTEGER | No | Yes |  |
| `event_id` | INTEGER | Yes | No |  |
| `media_type` | TEXT | No | No |  |
| `url` | TEXT | No | No |  |
| `title` | TEXT | No | No |  |
| `description` | TEXT | No | No |  |
| `source_id` | INTEGER | No | No |  |
| `created_at` | TIMESTAMP | No | No | CURRENT_TIMESTAMP |

## 🧩 Table: `EventOrgs`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `event_id` | INTEGER | No | No |  |
| `org_id` | INTEGER | No | No |  |
| `role` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |

## 🧩 Table: `EventPeople`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `event_id` | INTEGER | No | No |  |
| `person_id` | INTEGER | No | No |  |
| `role` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |

## 🧩 Table: `EventTags`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `event_id` | INTEGER | Yes | No |  |
| `tag` | TEXT | Yes | No |  |

## 🧩 Table: `Events`
> Captures significant historical events related to people, places, or the community. Includes date, location, type, and summary.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `title` | TEXT | Yes | No |  |
| `type` | TEXT | Yes | No |  |
| `scope` | TEXT | No | No | 'COMMUNITY' |
| `date` | TEXT | No | No |  |
| `date_precision` | TEXT | No | No |  |
| `end_date` | TEXT | No | No |  |
| `end_date_precision` | TEXT | No | No |  |
| `location` | TEXT | No | No |  |
| `address_id` | INTEGER | No | No |  |
| `description` | TEXT | No | No |  |
| `summary` | TEXT | No | No |  |
| `source_id` | INTEGER | No | No |  |
| `link_url` | TEXT | No | No |  |
| `created_at` | TIMESTAMP | No | No | CURRENT_TIMESTAMP |

## 🧩 Table: `GeoJSONData`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `geojson_id` | INTEGER | No | Yes |  |
| `geojson_text` | TEXT | Yes | No |  |
| `geojson_type` | TEXT | Yes | No |  |
| `feature_type` | TEXT | Yes | No |  |
| `description` | TEXT | No | No |  |
| `source` | TEXT | No | No |  |
| `start_date` | TEXT | No | No |  |
| `end_date` | TEXT | No | No |  |
| `created_date` | DATETIME | No | No | CURRENT_TIMESTAMP |
| `modified_date` | DATETIME | No | No |  |

## 🧩 Table: `GeoJSONLink`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `link_id` | INTEGER | No | Yes |  |
| `geojson_id` | INTEGER | Yes | No |  |
| `record_type` | TEXT | Yes | No |  |
| `record_id` | INTEGER | Yes | No |  |
| `legal_description_id` | INTEGER | No | No |  |
| `created_date` | DATETIME | No | No | CURRENT_TIMESTAMP |

## 🧩 Table: `LandAssessment`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `record_id` | INTEGER | No | Yes |  |
| `people_id` | INTEGER | Yes | No |  |
| `assessment_year` | INTEGER | Yes | No |  |
| `section` | TEXT | No | No |  |
| `township_id` | INTEGER | Yes | No |  |
| `acres` | TEXT | No | No |  |
| `acres_qtr` | TEXT | No | No |  |
| `rate_per_acre` | TEXT | No | No |  |
| `purchase_price` | TEXT | No | No |  |
| `purchaser_name` | TEXT | No | No |  |
| `date_of_sale` | TEXT | No | No |  |
| `receipt_number` | TEXT | No | No |  |
| `certificate_number` | TEXT | No | No |  |
| `to_whom_patented` | TEXT | No | No |  |
| `date_of_patent` | TEXT | No | No |  |
| `liber_page` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |

## 🧩 Table: `LandTransactions`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `seller_id` | INTEGER | No | No |  |
| `buyer_id` | INTEGER | No | No |  |
| `deed_amount` | REAL | No | No |  |
| `deed_type` | TEXT | No | No |  |
| `deed_recorded` | TEXT | No | No |  |
| `deed_dated` | TEXT | No | No |  |
| `deed_acknowledged` | TEXT | No | No |  |
| `transaction_date` | TEXT | No | No |  |
| `property_description` | TEXT | No | No |  |
| `property_address` | TEXT | No | No |  |
| `property_city` | TEXT | No | No |  |
| `property_state` | TEXT | No | No |  |
| `property_zip` | TEXT | No | No |  |
| `property_county` | TEXT | No | No |  |
| `property_geojson` | TEXT | No | No |  |

## 🧩 Table: `LegalDescriptions`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `description_id` | INTEGER | No | Yes |  |
| `deed_id` | INTEGER | Yes | No |  |
| `township_id` | INTEGER | Yes | No |  |
| `section_number` | INTEGER | No | No |  |
| `quarter_section` | TEXT | No | No |  |
| `quarter_quarter` | TEXT | No | No |  |
| `half` | TEXT | No | No |  |
| `acres` | DECIMAL | No | No |  |
| `description_text` | TEXT | Yes | No |  |
| `segment_order` | INTEGER | No | No |  |
| `created_date` | DATETIME | No | No | CURRENT_TIMESTAMP |
| `modified_date` | DATETIME | No | No |  |

## 🧩 Table: `LegalNoticeParties`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `notice_id` | INTEGER | No | No |  |
| `person_id` | INTEGER | No | No |  |
| `party_role` | TEXT | No | No |  |

## 🧩 Table: `LegalNotices`
> Captures legal announcements from newspapers or official documents, such as estate sales or court proceedings.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `notice_id` | INTEGER | No | Yes |  |
| `notice_type` | TEXT | No | No |  |
| `date_published` | TEXT | No | No |  |
| `execution_date` | TEXT | No | No |  |
| `legal_text` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |
| `property_description` | TEXT | No | No |  |
| `township_id` | INTEGER | No | No |  |
| `deed_id` | INTEGER | No | No |  |
| `source_id` | INTEGER | No | No |  |

## 🧩 Table: `LifeEvents`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `event_id` | INTEGER | No | Yes |  |
| `person_id` | INTEGER | Yes | No |  |
| `event_type` | TEXT | Yes | No |  |
| `event_title` | TEXT | No | No |  |
| `event_description` | TEXT | No | No |  |
| `event_date` | TEXT | No | No |  |
| `date_precision` | TEXT | No | No |  |
| `source_title` | TEXT | No | No |  |
| `source_link` | TEXT | No | No |  |
| `location` | TEXT | No | No |  |
| `created_at` | TEXT | No | No | CURRENT_TIMESTAMP |

## 🧩 Table: `MapAssets`
> Stores GeoJSON or KML-based map layers to visualize community infrastructure or landmarks.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `asset_id` | INTEGER | No | Yes |  |
| `asset_name` | TEXT | No | No |  |
| `asset_type` | TEXT | No | No |  |
| `coordinates_text` | TEXT | No | No |  |
| `description` | TEXT | No | No |  |

## 🧩 Table: `MapPlacemarks`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `placemark_id` | INTEGER | No | Yes |  |
| `placemark_name` | TEXT | No | No |  |
| `latitude` | REAL | No | No |  |
| `longitude` | REAL | No | No |  |
| `description` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |
| `placemark_type` | TEXT | No | No |  |
| `specific_attributes` | TEXT | No | No |  |

## 🧩 Table: `Marriages`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `m_id` | INTEGER | No | Yes |  |
| `person1_id` | INTEGER | No | No |  |
| `person2_id` | INTEGER | No | No |  |
| `m_date` | TEXT | No | No |  |
| `m_end_date` | TEXT | No | No |  |
| `m_location` | TEXT | No | No |  |
| `m_note` | TEXT | No | No |  |
| `m_link` | TEXT | No | No |  |

## 🧩 Table: `Mayor`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `mayor_id` | INTEGER | No | No |  |
| `mayor_term_start` | TEXT | No | No |  |
| `mayor_term_start_precision` | TEXT | No | No |  |
| `mayor_term_end` | TEXT | No | No |  |
| `mayor_term_end_precision` | TEXT | No | No |  |
| `mayor_election_link` | TEXT | No | No |  |

## 🧩 Table: `Media`
> Stores multimedia items (images, videos, documents) related to people, places, or events.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `description` | TEXT | No | No |  |
| `media_type` | TEXT | No | No |  |
| `url` | TEXT | No | No |  |
| `title` | TEXT | No | No |  |
| `date_created` | DATE | No | No |  |
| `author` | TEXT | No | No |  |
| `tags` | TEXT | No | No |  |
| `access` | TEXT | No | No |  |

## 🧩 Table: `MediaPerson`
> Linking table that associates people with media items.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `media_id` | INTEGER | No | No |  |
| `person_id` | INTEGER | No | No |  |

## 🧩 Table: `Membership`
> Links individuals to organizations with a role, time span, and optional notes.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `person_id` | INTEGER | No | No |  |
| `org_id` | INTEGER | No | No |  |
| `start_date` | DATE | No | No |  |
| `end_date` | DATE | No | No |  |
| `role` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |

## 🧩 Table: `Obituaries`
> Stores published obituaries for individuals, with publication details and optional text/source link.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `obit_id` | INTEGER | No | Yes |  |
| `person_id` | INTEGER | Yes | No |  |
| `source_title` | TEXT | No | No |  |
| `obit_text` | TEXT | No | No |  |
| `date_published` | TEXT | No | No |  |
| `source_link` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |
| `date_precision` | TEXT | No | No | 'EXACT' |


## 🧩 Table: `Org`
> Organization registry used for group affiliations (e.g., civic, religious, labor).

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `org_id` | INTEGER | No | Yes |  |
| `org_name` | TEXT | No | No |  |
| `org_desc` | TEXT | No | No |  |
| `org_type` | TEXT | No | No |  |
| `org_founded_date` | TEXT | No | No |  |

## 🧩 Table: `People`
> Central table for individuals in the system. Tracks full name, family relationships, vital dates, and occupation.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `first_name` | TEXT | No | No |  |
| `middle_name` | TEXT | No | No |  |
| `last_name` | TEXT | No | No |  |
| `title` | TEXT | No | No |  |
| `nick_name` | TEXT | No | No |  |
| `married_name` | TEXT | No | No |  |
| `married_to` | INTEGER | No | No |  |
| `father` | INTEGER | No | No |  |
| `mother` | INTEGER | No | No |  |
| `birth_date` | TEXT | No | No |  |
| `birth_location` | TEXT | No | No |  |
| `death_date` | TEXT | No | No |  |
| `death_location` | TEXT | No | No |  |
| `death_cause` | TEXT | No | No |  |
| `buried_date` | TEXT | No | No |  |
| `buried_location` | TEXT | No | No |  |
| `buried_notes` | TEXT | No | No |  |
| `buried_source` | TEXT | No | No |  |
| `marriage_date` | TEXT | No | No |  |
| `marriage_location` | TEXT | No | No |  |
| `business` | TEXT | No | No |  |
| `obit_link` | TEXT | No | No |  |
| `occupation` | TEXT | No | No |  |
| `bio` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |
| `buried_link` | TEXT | No | No |  |
| `buried_block` | TEXT | No | No |  |
| `buried_tour_link` | TEXT | No | No |  |

## 🧩 Table: `Photos`
> Links a person to image file paths (e.g., portraits or headstones).

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `person_id` | INTEGER | No | No |  |
| `image_path` | TEXT | No | No |  |

## 🧩 Table: `Property`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `property_id` | INTEGER | No | Yes |  |
| `owner_id` | INTEGER | No | No |  |
| `address_id` | INTEGER | No | No |  |
| `start_date` | DATE | No | No |  |
| `end_date` | DATE | No | No |  |
| `notes` | TEXT | No | No |  |
| `coordinates_text` | TEXT | No | No |  |

## 🧩 Table: `PropertyLineage`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `lineage_id` | INTEGER | No | Yes |  |
| `parent_deed_id` | INTEGER | No | No |  |
| `child_deed_id` | INTEGER | No | No |  |
| `relationship_type` | TEXT | No | No |  |
| `effective_date` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |

## 🧩 Table: `RecordTracking`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `person_id` | INTEGER | No | No |  |
| `checked_out_by` | TEXT | No | No |  |
| `check_out_date` | DATE | No | No |  |
| `expected_return_date` | DATE | No | No |  |
| `status` | TEXT | No | No |  |

## 🧩 Table: `ResGroupMembers`
> Links individuals to a specific Census or Residence group (e.g., same dwelling unit).

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `res_group_id` | INTEGER | No | No |  |
| `res_group_member` | INTEGER | No | No |  |
| `res_group_role` | TEXT | No | No |  |
| `member_order` | INTEGER | No | No |  |

## 🧩 Table: `ResGroups`
> Represents a shared residence or household unit used in Census records, with address and group metadata.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `address_id` | INTEGER | No | No |  |
| `res_group_start_date` | TEXT | No | No |  |
| `res_group_end_date` | TEXT | No | No |  |
| `household_notes` | TEXT | No | No |  |
| `res_group_year` | INTEGER | No | No |  |
| `event_type` | TEXT | No | No |  |
| `census_notes` | TEXT | No | No |  |
| `record_completed` | BOOLEAN | No | No | 0 |
| `township_id` | INTEGER | No | No |  |
| `dwelling_num` | INTEGER | No | No |  |
| `household_num` | INTEGER | No | No |  |

## 🧩 Table: `ResHistory`
> Linking table between people and their place of residence during a specific time period.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `res_history_id` | INTEGER | No | Yes |  |
| `person_id` | INTEGER | No | No |  |
| `residence_id` | INTEGER | No | No |  |

## 🧩 Table: `Residence`
> Unique records for address + date combinations. Serves as the shared anchor for people and census records.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `residence_id` | INTEGER | No | Yes |  |
| `address_id` | INTEGER | No | No |  |
| `start_date` | TEXT | No | No |  |
| `start_date_precision` | TEXT | No | No |  |
| `end_date` | TEXT | No | No |  |
| `end_date_precision` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |
| `res_source` | INTEGER | No | No |  |
| `res_link` | TEXT | No | No |  |

## 🧩 Table: `RotaryMembers`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `member_id` | INTEGER | No | Yes |  |
| `people_id` | INTEGER | No | No |  |
| `year_active` | INTEGER | No | No |  |
| `role` | TEXT | No | No |  |
| `awards` | TEXT | No | No |  |
| `projects` | TEXT | No | No |  |
| `photo_link` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |

## 🧩 Table: `Sources`
> Repository of citation information for external sources used in record justification.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `title` | TEXT | No | No |  |
| `author` | TEXT | No | No |  |
| `publisher` | TEXT | No | No |  |
| `pub_date` | TEXT | No | No |  |
| `note` | TEXT | No | No |  |

## 🧩 Table: `Tax_Records`
> Tax Records for individuals in the People table. Linked to the People table via people_id.
Also linked to the Address table via address_id and Townships table via township)id

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `record_id` | INTEGER | No | Yes |  |
| `people_id` | INTEGER | No | No |  |
| `year` | INTEGER | No | No |  |
| `description` | TEXT | No | No |  |
| `section` | TEXT | No | No |  |
| `acres` | TEXT | No | No |  |
| `acres_qtr` | TEXT | No | No |  |
| `prop_value` | TEXT | No | No |  |
| `personal_value` | TEXT | No | No |  |
| `notes` | TEXT | No | No |  |
| `address_id` | INTEGER | No | No |  |
| `township_id` | INTEGER | No | No |  |

## 🧩 Table: `TempFindAGraveResults`
> No description provided yet.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `id` | INTEGER | No | Yes |  |
| `first_name` | TEXT | No | No |  |
| `middle_name` | TEXT | No | No |  |
| `last_name` | TEXT | No | No |  |
| `married_name` | TEXT | No | No |  |
| `birth_date` | TEXT | No | No |  |
| `death_date` | TEXT | No | No |  |
| `findagrave_link` | TEXT | No | No |  |


## 🧩 Table: `Townships`
> Townships that are tracked within the scope of the local community. Linked to other township
records via the parent_township_id field.

| Column Name | Data Type | Not Null | Primary Key | Default Value |
|-------------|-----------|----------|-------------|----------------|
| `township_id` | INTEGER | No | Yes |  |
| `township_name` | TEXT | No | No |  |
| `township_number` | INTEGER | No | No |  |
| `township_direction` | TEXT | No | No |  |
| `range_number` | INTEGER | No | No |  |
| `range_direction` | TEXT | No | No |  |
| `start_date` | TEXT | No | No |  |
| `end_date` | TEXT | No | No |  |
| `parent_township_id` | INTEGER | No | No |  |
| `notes` | TEXT | No | No |  |
| `county` | TEXT | No | No |  |
| `state` | TEXT | No | No |  |


## 🧩 Table: `Institution`
> Core registry of institutions such as schools, hospitals, and churches.

| Column Name         | Data Type | Not Null | Primary Key | Default Value |
|---------------------|-----------|----------|-------------|----------------|
| `inst_id`           | INTEGER   | No       | Yes         |                |
| `inst_name`         | TEXT      | No       | No          |                |
| `inst_type`         | TEXT      | No       | No          |                |
| `inst_founding_date`| TEXT      | No       | No          |                |
| `inst_closing_date` | TEXT      | No       | No          |                |
| `inst_description`  | TEXT      | No       | No          |                |
| `inst_website`      | TEXT      | No       | No          |                |
| `inst_image_path`   | TEXT      | No       | No          |                |
| `inst_external_url` | TEXT      | No       | No          |                |
| `inst_notes`        | TEXT      | No       | No          |                |

---

## 🧩 Table: `Inst_Lineage`
> Tracks renaming, merging, or splitting history of institutions.

| Column Name     | Data Type | Not Null | Primary Key | Default Value |
|-----------------|-----------|----------|-------------|----------------|
| `lineage_id`    | INTEGER   | No       | Yes         |                |
| `inst_id`       | INTEGER   | No       | No          |                |
| `related_inst_id` | INTEGER | No       | No          |                |
| `lineage_type`  | TEXT      | No       | No          |                |
| `lineage_notes` | TEXT      | No       | No          |                |

---

## 🧩 Table: `Inst_Location`
> Records the physical address history of an institution.

| Column Name         | Data Type | Not Null | Primary Key | Default Value |
|---------------------|-----------|----------|-------------|----------------|
| `inst_location_id`  | INTEGER   | No       | Yes         |                |
| `inst_id`           | INTEGER   | No       | No          |                |
| `address_id`        | INTEGER   | No       | No          |                |
| `location_start_date` | TEXT    | No       | No          |                |
| `location_end_date` | TEXT     | No       | No          |                |
| `location_notes`    | TEXT     | No       | No          |                |

---

## 🧩 Table: `Inst_Affiliation`
> Links individuals to institutions by role (e.g., teacher, student, janitor).

| Column Name               | Data Type | Not Null | Primary Key | Default Value |
|---------------------------|-----------|----------|-------------|----------------|
| `inst_affiliation_id`     | INTEGER   | No       | Yes         |                |
| `inst_id`                 | INTEGER   | No       | No          |                |
| `person_id`               | INTEGER   | No       | No          |                |
| `inst_affiliation_role`   | TEXT      | No       | No          |                |
| `inst_affiliation_start_date` | TEXT  | No       | No          |                |
| `inst_affiliation_end_date` | TEXT    | No       | No          |                |
| `inst_affiliation_notes` | TEXT      | No       | No          |                |
| `source_id`               | INTEGER   | No       | No          |                |

---

## 🧩 Table: `InstRole`
> Lookup table for standardized roles within institutions.

| Column Name     | Data Type | Not Null | Primary Key | Default Value |
|-----------------|-----------|----------|-------------|----------------|
| `inst_role`     | TEXT      | Yes      | Yes         |                |
| `role_category` | TEXT      | No       | No          |                |
| `role_description` | TEXT   | No       | No          |                |