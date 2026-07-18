import { render, screen } from "@testing-library/react";
import { PipelineProgress } from "@/components/PipelineProgress";

describe("PipelineProgress", () => {
  it("renders progress percentage", () => {
    render(<PipelineProgress stage="cleaning" progress={16} />);
    expect(screen.getByText("16%")).toBeInTheDocument();
  });

  it("marks current stage as active", () => {
    render(<PipelineProgress stage="eda" progress={32} />);
    expect(screen.getByText(/EDA/)).toBeInTheDocument();
  });

  it("renders all stages", () => {
    render(<PipelineProgress stage="complete" progress={100} />);
    expect(screen.getByText(/Profiling/)).toBeInTheDocument();
    expect(screen.getByText(/PDF/)).toBeInTheDocument();
  });
});
