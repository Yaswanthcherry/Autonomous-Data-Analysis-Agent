import { formatBytes, formatDate } from "@/lib/utils";

describe("formatBytes", () => {
  it("formats bytes", () => expect(formatBytes(500)).toBe("500 B"));
  it("formats kilobytes", () => expect(formatBytes(2048)).toBe("2.0 KB"));
  it("formats megabytes", () => expect(formatBytes(1_500_000)).toBe("1.4 MB"));
});

describe("formatDate", () => {
  it("returns a non-empty string", () => {
    const result = formatDate("2024-01-15T10:30:00Z");
    expect(typeof result).toBe("string");
    expect(result.length).toBeGreaterThan(0);
  });
});
