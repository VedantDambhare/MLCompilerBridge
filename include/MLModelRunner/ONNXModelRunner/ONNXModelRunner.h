//=== MLModelRunner/ONNXModelRunner/ONNXModelRunner.h - C++ --------------===//
//
// Part of the MLCompilerBridge Project, under the Apache 2.0 License.
// See the LICENSE file under home directory for license and copyright
// information.
//
//===----------------------------------------------------------------------===//
//
// ONNXModelRunner class supporting communication via ONNX C++ Runtime.
// Only inference is supported.
//
// This class interfaces with Environment and Agent classes to support
// ML/RL model inference via ONNXModel.
//
// Usage:
// 1. Construct an ONNXModelRunner object with the environment and the agents.
//    Environment and agents are created by the user by inheriting from the
//    Environment class and using the Agent class.
// 2. Multiple agents can be added to the ONNXModelRunner object using the
//    addAgent() method. The agents are identified by a unique name.
// 3. Call evaluate() to get the result from the model.
//
// Internally the ONNXModelRunner object will call the step() method of the
// environment to get the next observation and the computeAction() method of the
// agent to get the action corresponding to the observation.
//
//===----------------------------------------------------------------------===//

#ifndef ONNX_MODELRUNNER_H
#define ONNX_MODELRUNNER_H

#include "MLModelRunner/MLModelRunner.h"
#include "MLModelRunner/ONNXModelRunner/agent.h"
#include "MLModelRunner/ONNXModelRunner/environment.h"

namespace MLBridge {
class ONNXModelRunner : public MLModelRunner {
public:
  ONNXModelRunner(MLBridge::Environment *env,
                  std::map<std::string, Agent *> agents,
                  llvm::LLVMContext *Ctx = nullptr);

  void setEnvironment(MLBridge::Environment *_env) { env = _env; }
  MLBridge::Environment *getEnvironment() { return env; }

  void addAgent(Agent *agent, std::string name);
  void computeAction(Observation &obs);

  void requestExit() override {}

  void *evaluateUntyped() override;

private:
  MLBridge::Environment *env;
  std::map<std::string, Agent *> agents;
};
} // namespace MLBridge
#endif // ONNX_MODELRUNNER_H
