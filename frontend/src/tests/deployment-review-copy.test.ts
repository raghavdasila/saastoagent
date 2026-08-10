import { expect, it } from "vitest";

import { hostedAgentReviewCopy } from "../features/delivery/DeploymentReviewSurface";


it("keeps each hosted Agent review consequence exact", () => {
  expect(hostedAgentReviewCopy("deploy")).toMatchObject({
    heading: "Approve hosted Agent deployment",
    accept: "Deploy reviewed build",
  });
  expect(hostedAgentReviewCopy("rollback")).toMatchObject({
    heading: "Approve hosted Agent rollback",
    accept: "Roll back to reviewed deployment",
  });
  expect(hostedAgentReviewCopy("availability")).toEqual({
    heading: "Approve hosted Web availability change",
    consequence: "Approval applies the exact reviewed enable or disable choice. Rejection leaves the channel availability unchanged.",
    accept: "Apply availability change",
    reject: "Keep current availability",
  });
});
