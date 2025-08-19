Dates
=====

Files with dates to be used to generate the historical timeline. Each YAML file
is an array of related people or events.

Format
------

All dates use an extended ISO 8601 format with negative years for BCE.
Approximate dates can use the "c. " prefix. Partial dates may omit the month
or day.

### General Fields

- **`Label`**: Display name or title shown on timeline
- **`Keywords`**: CSS classes for styling and categorization

### Time periods
- **`Start`**: Start date (requires `End`)
- **`End`**: End date (requires `Start`)

### Lives

- **`DOB`**: Date of birth (requires `DOD` or `Alive`)
- **`DOD`**: Date of death (requires `DOB`, cannot be present with `Alive`)
- **`Alive`**: Indicates that the person is currently alive and there is no date
               of death (requires `DOB`, cannot be present with `DOD`)
