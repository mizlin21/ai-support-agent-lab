# KB-006: Report Generation Timeout

## Symptoms
- Reports fail to generate
- Timeout error occurs during report creation
- Large datasets fail to load

## Likely Causes
- Large dataset causing long processing time
- Backend performance limitations
- Temporary system load spike

## Resolution Steps
1. Reduce the size of the dataset if possible (filter data)
2. Try generating the report during off-peak hours
3. Refresh the page and retry
4. Break report into smaller segments if supported

## Escalate If
- Reports fail consistently regardless of size
- Timeout occurs immediately on execution
- Multiple users experience the same issue

## Tags
reporting, timeout, performance, data