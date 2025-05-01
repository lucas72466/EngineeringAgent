
import numpy as np
import control as ctrl
import math

def check_stability(omega_L, beta_b, num, den):
    G = ctrl.TransferFunction(num, den)
    # Calculate |G(jω_c)|
    mag_c, phase_c, _ = ctrl.frequency_response(G, omega_L)
    # Compute proportional gain controller
    K_p = 1 / np.abs(mag_c)[0]
    # Integral boost Ki(s)
    Ki = ctrl.TransferFunction([beta_b, omega_L], [math.sqrt(beta_b*beta_b + 1), 0])
    # Final controller
    K = K_p * Ki 
    # Performance Check
    L = G * K
    # Closed-loop transfer function
    T = ctrl.feedback(L, 1)
    poles = ctrl.poles(T)
    return np.all(np.real(poles) < -0.01)

def check_stability_pid(omega_L, beta_b, beta_l, num, den):
    G = ctrl.TransferFunction(num, den)
    # Calculate |G(jω_c)|
    mag_c, phase_c, _ = ctrl.frequency_response(G, omega_L)
    # Compute proportional gain controller
    K_p = 1 / np.abs(mag_c)[0]
    # Integral boost Ki(s)
    Ki = ctrl.TransferFunction([beta_b, omega_L], [math.sqrt(beta_b*beta_b + 1), 0])
    # Add a lead compensator with adjusted beta
    if beta_l != "NA":
        Kl = ctrl.TransferFunction([beta_l, omega_L], [1, beta_l * omega_L])
    else:
        Kl = 1
    # Final controller
    K = K_p * Ki * Kl
    # Performance Check
    L = G * K
    # Closed-loop transfer function
    T = ctrl.feedback(L, 1)
    poles = ctrl.poles(T)
    return np.all(np.real(poles) < -0.01)

def loop_shaping(omega_L, beta_b, num, den):
    # Define the transfer function G(s)
    G = ctrl.TransferFunction(num, den)
    # Calculate |G(jω_c)|
    mag_c, phase_c, _ = ctrl.frequency_response(G, omega_L)
    # Compute proportional gain controller
    K_p = 1 / np.abs(mag_c)[0]
    # Integral boost Ki(s)
    Ki = ctrl.TransferFunction([beta_b, omega_L], [math.sqrt(beta_b*beta_b + 1), 0])
    # Final controller
    K = K_p * Ki 
    # Performance Check
    L = G * K
    # Closed-loop transfer function
    sys = ctrl.feedback(L, 1)
    # Get the step response of the closed-loop system T(s)
    T_out, T_time = ctrl.step_response(sys)
    T = np.linspace(0, 500, 10000)  # More time points for better resolution
    info = ctrl.step_info(sys)
    # Gain margin and phase margin
    gm, pm, wg, wp = ctrl.margin(L)
    # Steady-state error (assuming unit step input)
    ess = 1 / (1 + np.abs(ctrl.dcgain(L)))
    return gm, pm, info['RiseTime'], info['SettlingTime'], info['Overshoot'], ess



def check_stability_baseline(K_num, K_den, num, den):
    G = ctrl.TransferFunction(num, den)
    # Define the transfer function K(s)
    K = ctrl.TransferFunction(K_num, K_den)
    # Performance Check
    L = G * K
    # Closed-loop transfer function
    T = ctrl.feedback(L, 1)
    poles = ctrl.poles(T)
    return np.all(np.real(poles) < -0.001)



def compute_settling_time(sys, tol=0.02):
    # Generate the step response
    T, yout = ctrl.step_response(sys,T=20)
    
    # Approximate the final value as the last value in the response
    final_value = yout[-1]
    
    # Determine the tolerance band (e.g., 2% of the final value)
    lower_bound = final_value * (1 - tol)
    upper_bound = final_value * (1 + tol)
    
    # Find the time index where the response enters the tolerance band and stays within it
    for i in range(len(yout)):
        if np.all(yout[i:] >= lower_bound) and np.all(yout[i:] <= upper_bound):
            settling_time = T[i]
            return settling_time
    
    # If the settling time is not found, return None or an indication of failure
    return None

def performance_eval(K_num, K_den, num, den):
    # Define the transfer function G(s)
    G = ctrl.TransferFunction(num, den)
    # Define the transfer function K(s)
    K = ctrl.TransferFunction(K_num, K_den)
    # Performance Check
    L = G * K
    # Closed-loop transfer function
    sys = ctrl.feedback(L, 1)
    # # Get the step response of the closed-loop system T(s)
    # T_out, T_time = ctrl.step_response(sys)
    # # print(T_out)
    # T = 50000

    info = ctrl.step_info(sys)
    # Gain margin and phase margin
    gm, pm, wg, wp = ctrl.margin(L)
    # Steady-state error (assuming unit step input)
    ess = 1 / (1 + np.abs(ctrl.dcgain(L)))
    # SettlingTime = compute_settling_time(sys)
    return gm, pm, info['SettlingTime']





def loop_shaping_pid(omega_L, beta_b, beta_l, num, den):
    # Define the transfer function G(s)
    G = ctrl.TransferFunction(num, den)
    # Calculate |G(jω_c)|
    mag_c, phase_c, _ = ctrl.frequency_response(G, omega_L)
    # Compute proportional gain controller
    K_p = 1 / np.abs(mag_c)[0]
    # Integral boost Ki(s)
    Ki = ctrl.TransferFunction([beta_b, omega_L], [math.sqrt(beta_b*beta_b + 1), 0])
    # Add a lead compensator with adjusted beta
    if beta_l != "NA":
        Kl = ctrl.TransferFunction([beta_l, omega_L], [1, beta_l * omega_L])
    else:
        Kl = 1
    # Final controller
    K = K_p * Ki * Kl
    # Performance Check
    L = G * K
    # Closed-loop transfer function
    sys = ctrl.feedback(L, 1)
    # Get the step response of the closed-loop system T(s)
    T_out, T_time = ctrl.step_response(sys)
    info = ctrl.step_info(sys, 200)
    # Gain margin and phase margin
    gm, pm, wg, wp = ctrl.margin(L)
    # Steady-state error (assuming unit step input)
    ess = 1 / (1 + np.abs(ctrl.dcgain(L)))
    return gm, pm, info['RiseTime'], info['SettlingTime'], info['Overshoot'], ess


def feedback_prompt(design_memory, thresholds):
    designs = design_memory.get_all_designs()
    prompt = "Here are the designs and their performances:\n"
    
    for i, design in enumerate(designs, 1):
        parameters = ', '.join(f"{key}={value}" for key, value in design['parameters'].items())
        performance = ', '.join(f"{key}={value}" if value != "unstable" else "unstable" for key, value in design['performance'].items())
        
        # Check against thresholds and generate feedback
        feedback = []
        if "unstable" in design['performance'].values():
            feedback.append("Your design is unstable, there are unstable poles. Please redesign!")
        else:
            for metric, specs in thresholds.items():
                value = design['performance'].get(metric)
                if value is not None:
                    if 'min' in specs and value < specs['min']:
                        feedback.append(specs['message'])
                    elif 'max' in specs and value > specs['max']:
                        feedback.append(specs['message'])

        prompt += f"### Design {i}\nParameters: {parameters}\nPerformance: {performance}\n"
        if feedback:
            prompt += "Feedback: " + " ".join(feedback) + "\n"
        prompt += "\n"
        
    prompt += "Based on the above designs, what improvements would you suggest for the next iteration?"
    return prompt


def feedback_prompt_wo_history(design_memory, thresholds):
    designs = design_memory.get_all_designs()
    prompt = "Here are the history designs and the feedbacks based on the previsous designs:\n"
    
    for i, design in enumerate(designs, 1):
        parameters = ', '.join(f"{key}={value}" for key, value in design['parameters'].items())
        performance = ', '.join(f"{key}={value}" if value != "unstable" else "unstable" for key, value in design['performance'].items())
        
        # Check against thresholds and generate feedback
        feedback = []
        if "unstable" in design['performance'].values():
            feedback.append("Your design is unstable, there are unstable poles. Please redesign!")
        else:
            for metric, specs in thresholds.items():
                value = design['performance'].get(metric)
                if value is not None:
                    if 'min' in specs and value < specs['min']:
                        feedback.append(specs['message'])
                    elif 'max' in specs and value > specs['max']:
                        feedback.append(specs['message'])

        prompt += f"### Design {i}\nParameters: {parameters}\n"
        if feedback:
            prompt += "Feedback: " + " ".join(feedback) + "\n"
        prompt += "\n"
        
    prompt += "Based on the above designs, what improvements would you suggest for the next iteration?"
    return prompt



def feedback_prompt_wo_feedback(design_memory, thresholds):
    designs = design_memory.get_all_designs()
    prompt = "Here are the history designs:\n"
    
    for i, design in enumerate(designs, 1):
        parameters = ', '.join(f"{key}={value}" for key, value in design['parameters'].items())
        performance = ', '.join(f"{key}={value}" if value != "unstable" else "unstable" for key, value in design['performance'].items())
        
        # Check against thresholds and generate feedback
        feedback = []
        if "unstable" in design['performance'].values():
            feedback.append("Your design is unstable, there are unstable poles. Please redesign!")
        else:
            for metric, specs in thresholds.items():
                value = design['performance'].get(metric)
                if value is not None:
                    if 'min' in specs and value < specs['min']:
                        feedback.append(specs['message'])
                    elif 'max' in specs and value > specs['max']:
                        feedback.append(specs['message'])

        prompt += f"### Design {i}\nParameters: {parameters}\nPerformance: {performance}\n"
        
    prompt += "Based on the above designs, what improvements would you suggest for the next iteration?"
    return prompt


def loop_shaping_w_delay(omega_L, beta_b, num, den, tau):
    # Define the transfer function G(s)
    G = ctrl.TransferFunction(num, den)
    
    # Use Pade approximation for the time delay
    pade_num, pade_den = ctrl.pade(tau, 5)  # 5th-order Pade approximation
    delay_approx = ctrl.TransferFunction(pade_num, pade_den)
    
    # Incorporate the delay into the transfer function G(s)
    G_delayed = G * delay_approx
    
    # Calculate |G(jω_L)| with the delay included
    mag_c, phase_c, _ = ctrl.frequency_response(G_delayed, omega_L)
    
    # Compute proportional gain controller
    K_p = 1 / np.abs(mag_c)[0]
    
    # Integral boost Ki(s)
    Ki = ctrl.TransferFunction([beta_b, omega_L], [math.sqrt(beta_b * beta_b + 1), 0])

    # if beta_l != "NA":
    #     Kl = ctrl.TransferFunction([beta_l, omega_L], [1, beta_l * omega_L])
    # else:
    #     Kl = 1
    
    # Final controller
    K = K_p * Ki 
    
    # Performance Check
    L = G_delayed * K
    
    # Closed-loop transfer function
    sys = ctrl.feedback(L, 1)
    

    # Step response information
    info = ctrl.step_info(sys)
    
    # Gain margin and phase margin
    gm, pm, wg, wp = ctrl.margin(L)
    
    # Steady-state error (assuming unit step input)
    ess = 1 / (1 + np.abs(ctrl.dcgain(L)))
    
    return gm, pm, info['RiseTime'], info['SettlingTime'], info['Overshoot'], ess




def performance_eval_w_delay(K_num, K_den, num, den, tau):
    # Define the transfer function G(s)
    G = ctrl.TransferFunction(num, den)

    # Use Pade approximation for the time delay
    pade_num, pade_den = ctrl.pade(tau, 5)  # 5th-order Pade approximation
    delay_approx = ctrl.TransferFunction(pade_num, pade_den)

    G = G * delay_approx
    # Define the transfer function K(s)
    K = ctrl.TransferFunction(K_num, K_den)
    # Performance Check
    L = G * K
    # Closed-loop transfer function
    sys = ctrl.feedback(L, 1)
    # # Get the step response of the closed-loop system T(s)
    # T_out, T_time = ctrl.step_response(sys)
    # # print(T_out)
    # T = 50000

    try:
        # Try to compute the step info
        info = ctrl.step_info(sys, 200)
        settling_time = info['SettlingTime']
    except Exception as e:
        # If an error occurs, print the error message and return None or a default value
        print(f"An error occurred while calculating step info: {e}")
        settling_time = 10e5

    # Gain margin and phase margin
    gm, pm, wg, wp = ctrl.margin(L)
    # Steady-state error (assuming unit step input)
    ess = 1 / (1 + np.abs(ctrl.dcgain(L)))
    # SettlingTime = compute_settling_time(sys)
    return gm, pm, settling_time