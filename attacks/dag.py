'''
Function for Dense Adversarial Generation
Adversarial Examples for Semantic Segmentation
Muhammad Ferjad Naeem
ferjad.naeem@tum.de
adapted from https://github.com/IFL-CAMP/dense_adversarial_generation_pytorch
'''
import torch

def make_one_hot(labels, num_classes, device):
    '''
    Converts an integer label to a one-hot values.
    Parameters
    ----------
        labels : N x H x W, where N is batch size.(torch.Tensor)
        num_classes : int
        device: torch.device information
    -------
    Returns
        target : torch.Tensor on given device
        N x C x H x W, where C is class number. One-hot encoded.
    '''
    
    labels=labels.unsqueeze(1)
    one_hot = torch.FloatTensor(labels.size(0), num_classes, labels.size(2), labels.size(3)).zero_()
    one_hot = one_hot.to(device)
    target = one_hot.scatter_(1, labels.data, 1) 
    return target

def DAG(model,image,ground_truth,adv_target,num_iterations=20,gamma=0.07,no_background=True,background_class=0,device='cuda:0',verbose=False):
    '''
    Generates adversarial example for a given Image
    
    Parameters
    ----------
        model: Torch Model
        image: Torch tensor of dtype=float. Requires gradient. [b*c*h*w]
        ground_truth: Torch tensor of labels as one hot vector per class
        adv_target: Torch tensor of dtype=float. This is the purturbed labels. [b*classes*h*w]
        num_iterations: Number of iterations for the algorithm
        gamma: epsilon value. The maximum Change possible.
        no_background: If True, does not purturb the background class
        background_class: The index of the background class. Used to filter background
        device: Device to perform the computations on
        verbose: Bool. If true, prints the amount of change and the number of values changed in each iteration
    Returns
    -------
        Image:  Adversarial Output, logits of original image as torch tensor
        logits: Output of the Clean Image as torch tensor
        noise_total: List of total noise added per iteration as numpy array
        noise_iteration: List of noise added per iteration as numpy array
        prediction_iteration: List of prediction per iteration as numpy array
        image_iteration: List of image per iteration as numpy array

    '''
    image.requires_grad_()
    ground_truth = make_one_hot(ground_truth, 2, device)
    noise_total=[]
    noise_iteration=[]
    prediction_iteration=[]
    image_iteration=[]
    background=None
    logits=model(image)
    orig_image=image
    _,predictions_orig=torch.max(logits,1)
    predictions_orig=make_one_hot(predictions_orig,logits.shape[1],device)
    
    if(no_background):
        background=torch.zeros(logits.shape)
        background[:,background_class,:,:]=torch.ones((background.shape[2],background.shape[3]))
        background=background.to(device)
    
    for a in range(num_iterations):
        output=model(image)
        _,predictions=torch.max(output,1)
        prediction_iteration.append(predictions[0].cpu().numpy())
        predictions=make_one_hot(predictions,logits.shape[1],device)

        condition1=torch.eq(predictions,ground_truth)
        condition=condition1
       
        if no_background:
            condition2=(ground_truth!=background)
            condition=torch.mul(condition1,condition2)
        condition=condition.float()

        if(condition.sum()==0):
            # print("Condition Reached")
            # image=None
            break
        
        #Finding pixels to purturb
        adv_log=torch.mul(output,adv_target)
        #Getting the values of the original output
        clean_log=torch.mul(output,ground_truth)

        #Finding r_m
        adv_direction=adv_log-clean_log
        r_m=torch.mul(adv_direction,condition)
        r_m.requires_grad_()
        #Summation
        r_m_sum=r_m.sum()
        r_m_sum.requires_grad_()
        #Finding gradient with respect to image
        r_m_grad=torch.autograd.grad(r_m_sum,image,retain_graph=True)
        #Saving gradient for calculation
        r_m_grad_calc=r_m_grad[0]
        
        #Calculating Magnitude of the gradient
        r_m_grad_mag=r_m_grad_calc.norm()
        
        if(r_m_grad_mag==0):
            # print("Condition Reached, no gradient")
            #image=None
            break
        #Calculating final value of r_m
        r_m_norm=(gamma/r_m_grad_mag)*r_m_grad_calc

        #if no_background:
        #if False:
        if no_background is False:
            condition_image=condition.sum(dim=1)
            condition_image=condition_image.unsqueeze(1)
            r_m_norm=torch.mul(r_m_norm,condition_image)

        #Updating the image
        #print("r_m_norm : ",torch.unique(r_m_norm))
        image=torch.clamp((image+r_m_norm),0,1)
        image_iteration.append(image[0][0].detach().cpu().numpy())
        noise_total.append((image-orig_image)[0][0].detach().cpu().numpy())
        noise_iteration.append(r_m_norm[0][0].cpu().numpy())

        if verbose:
            print("Iteration ",a)
            print("Change to the image is ",r_m_norm.sum())
            print("Magnitude of grad is ",r_m_grad_mag)
            print("Condition 1 ",condition1.sum())
            if no_background:
                print("Condition 2 ",condition2.sum())
                print("Condition is", condition.sum()) 

    return image, logits, noise_total, noise_iteration, prediction_iteration, image_iteration