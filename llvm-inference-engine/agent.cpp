#include "agent.h"
#include "llvm/Support/raw_ostream.h"

#include <algorithm>
#include <cmath>
#include <iterator>

Agent::Agent(std::string modelPath, int input_size) {
  // Create model object here
  this->model = new ONNXModel(modelPath.c_str());
  this->input_size = input_size;
}

unsigned Agent::computeAction(Observation &input) {
  // Call model on input
  LLVM_DEBUG(llvm::errs() << "input.size() = " << input.size() << "\n");
  assert(input.size() > 0);
  llvm::SmallVector<float, 100> model_output;
  this->model->run(input, model_output);

  // select action from model output
  auto max = std::max_element(model_output.begin(),
                              model_output.end()); // [2, 4)
  int argmaxVal = std::distance(model_output.begin(), max);

  LLVM_DEBUG(llvm::errs() << "---------------MODEL OUTPUT VECTOR:----------------\n");
  for (auto e : model_output) {
    LLVM_DEBUG(llvm::errs() << e << " ");
  }
  llvm::errs() << "\nmax value and index are " << *max << " " << argmaxVal
               << "\n";
  return argmaxVal;
}