'''
    All 50 fps averages
    Res = [320, 240]
    270:
    x_t = 28
    blend_frac = 0.5
    All included            7.481536886681234
                            7.39539110791662
                            7.470236206647839
                            7.37025647821311
                            7.338197829131932
                            7.493975043886862
                            7.412638302686944
                            7.3773832788859455
                            7.572750555326978
                            7.609419321700687

    No cv2.remaps           8.815346927673435
                            8.745464002095302
                            8.770810562729297
                            8.603178524084296
                            8.633258643439396
                            8.538203712038635
                            8.745804894970268
                            8.664541557673793
                            8.492769642828485
                            8.630696139805101

    No combine              18.1113930647601
                            18.790385070749767
                            18.671361272073582
                            19.149283829387524
                            19.439207178153655
                            17.784815171143304
                            18.55560105870366
                            19.1758845060613
                            18.963291079211793
                            19.787911213528748
                            18.299348000670186
                            18.19878807084171
                            19.679988380148952
                            19.508250936537237

    Send empty to pc        9.155580718858571
                            9.548998278931453
                            9.29267198418027
                            9.129888027308784
                            9.511885075843674
                            9.14334858016564
                            9.289278718334485
                            9.074559487042269
                            8.931262655204735
                            8.965504990918697

    No receive from helper  9.639257847648478
                            9.892290162575426
                            9.762446322338622
                            9.65123094746227
                            9.701505683404264
                            9.494584641618982
                            9.482615105986076
                            9.321774305190939
                            9.407854419720465
                            8.946190891025516
                            9.098598130201093
                            8.890724525944751
                            8.991063949739853
'''
spacer = "----------------------"

fps_all = [7.481536886681234,
            7.39539110791662,
            7.470236206647839,
            7.37025647821311,
            7.338197829131932,
            7.493975043886862,
            7.412638302686944,
            7.3773832788859455,
            7.572750555326978,
            7.609419321700687]

fps_no_remap = [8.815346927673435,
            8.745464002095302,
            8.770810562729297,
            8.603178524084296,
            8.633258643439396,
            8.538203712038635,
            8.745804894970268,
            8.664541557673793,
            8.492769642828485,
            8.630696139805101]

fps_no_combine = [18.1113930647601,
            18.790385070749767,
            18.671361272073582,
            19.149283829387524,
            19.439207178153655,
            17.784815171143304,
            18.55560105870366,
            19.1758845060613,
            18.963291079211793,
            19.787911213528748,
            18.299348000670186,
            18.19878807084171,
            19.679988380148952,
            19.508250936537237]

fps_send_empty_to_pc = [9.155580718858571,
            9.548998278931453,
            9.29267198418027,
            9.129888027308784,
            9.511885075843674,
            9.14334858016564,
            9.289278718334485,
            9.074559487042269,
            8.931262655204735,
            8.965504990918697]

fps_no_receive_from_helper = [9.639257847648478,
            9.892290162575426,
            9.762446322338622,
            9.65123094746227,
            9.701505683404264,
            9.494584641618982,
            9.482615105986076,
            9.321774305190939,
            9.407854419720465,
            8.946190891025516,
            9.098598130201093,
            8.890724525944751,
            8.991063949739853]

def take_average(ar):
    return sum(ar)/len(ar)

fps_all = take_average(fps_all)
fps_no_remap = take_average(fps_no_remap)
fps_no_combine = take_average(fps_no_combine)
fps_send_empty_to_pc = take_average(fps_send_empty_to_pc)
fps_no_receive_from_helper = take_average(fps_no_receive_from_helper)

print("fps without certain operation")
print("all", fps_all)
print("no remap:", fps_no_remap)
print("no combine:", fps_no_combine)
print("no send to pc:", fps_send_empty_to_pc)
print("no receive from helper:", fps_no_receive_from_helper)

# ft = frametime in seconds
ft_all = 1/fps_all
ft_no_remap = 1/fps_no_remap
ft_no_combine = 1/fps_no_combine
ft_send_empty_to_pc = 1/fps_send_empty_to_pc
ft_no_receive_from_helper = 1/fps_no_receive_from_helper

print(spacer)
print("frametimes without certain operation")
print("all", ft_all)
print("no remap:", ft_no_remap)
print("no combine:",ft_no_combine)
print("no send to pc:", ft_send_empty_to_pc)
print("no receive from helper:", ft_no_receive_from_helper)

def complement(ft):
    return ft_all - ft

ft_remap = complement(ft_no_remap)
ft_combine = complement(ft_no_combine)
ft_send_img_to_pc = complement(ft_send_empty_to_pc)
ft_receive_from_helper = complement(ft_no_receive_from_helper)

print(spacer)
print("frametimes")
print("remap:", ft_remap)
print("combine:", ft_combine)
print("send_img_to pc:", ft_send_img_to_pc)
print("rec from helper:", ft_receive_from_helper)
ft_all_from_parts = sum((ft_remap, ft_combine, ft_send_img_to_pc, ft_receive_from_helper))
print("sum=", ft_all_from_parts)

print(spacer)
print("total error=", abs(ft_all-ft_all_from_parts), "secs/frame = ", abs(ft_all-ft_all_from_parts)/ft_all * 100, "%")

print(spacer)
print("time fractions")
def timefrac(ft):
    return ft/ft_all_from_parts
print("remap:               ", timefrac(ft_remap))
print("combine:             ", timefrac(ft_combine))
print("send_img_to_pc:      ", timefrac(ft_send_img_to_pc))
print("receive_img_helper:  ", timefrac(ft_receive_from_helper))
