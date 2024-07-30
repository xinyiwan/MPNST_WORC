import pandas as pd
from analysis_utils import get_rad, get_list_from_text, get_mean_volume, mean_confidence_interval
from sklearn.metrics import confusion_matrix,accuracy_score

date = '1214'

# function to ensemble the results from radiologists and models
def ensemble_model_cv(operation):

    # Get info
    cv_pids, y_predictions, y_truths = get_list_from_text()

    accuracys_1,accuracys_2 = [],[]
    sensitivitys_1,sensitivitys_2 = [],[]
    specificitys_1,specificitys_2 = [],[]
    # Extract info in each cross-valiation
    for i in range(len(y_truths)):

        # Get gt, results from model and radiologist David
        pids = cv_pids[i]
        y = y_truths[i]
        y_test = y_predictions[i]

        if 'MPNSTRad-001_1' in pids:
            index = pids.index('MPNSTRad-001_1')
            del pids[index]
            del y[index]
            del y_test[index]

        y_rad_1, missing_id_1 = get_rad(pids,1)
        y_rad_2, missing_id_2 = get_rad(pids,2)

        missing_ids = missing_id_1 + missing_id_2

        for mid in missing_ids:
            index = pids.index(mid)
            del pids[index]
            del y[index]
            del y_test[index]
        #
        print(f"test1: {y_rad_1}")
        print(f"test2: {y_rad_2}")
        print(f"test3: {y_test}")
        y_or_1 = []
        y_or_2 = []

        for j in range(len(pids)):
            # Or
            if operation == 'OR':
                y_new_1 = y_test[j] | y_rad_1[j]

            if operation == 'AND':
                y_new_1 = y_test[j] & y_rad_1[j]

            y_or_1.append(y_new_1)
        

        for j in range(len(pids)):
            # Or
            if operation == 'OR':
                y_new_2 = y_test[j] | y_rad_2[j]

            if operation == 'AND':
                y_new_2 = y_test[j] & y_rad_2[j]

            y_or_2.append(y_new_2)
        
        # print(f"test4: {y_or_1}")
        # print(f"test5: {y_or_2}")
        # print(f"truth: {y}")

        # Get evaluations for rad 1    
        tn, fp, fn, tp = confusion_matrix(y, y_or_1).ravel()
        specificity = tn / (tn+fp)
        sensitivity = tp / (fn+tp)
        accuracy = accuracy_score(y, y_or_1)

        specificitys_1.append(specificity)
        sensitivitys_1.append(sensitivity)
        accuracys_1.append(accuracy)

        # Get evaluations for rad 2       
        tn, fp, fn, tp = confusion_matrix(y, y_or_2).ravel()
        specificity = tn / (tn+fp)
        sensitivity = tp / (fn+tp)
        accuracy = accuracy_score(y, y_or_2)


        specificitys_2.append(specificity)
        sensitivitys_2.append(sensitivity)
        accuracys_2.append(accuracy)

    # Save data 
    data = pd.DataFrame()
    data['T1_rad1'] = ['{:.2f},[{:.2f},{:.2f}]'.format(mean_confidence_interval(accuracys_1)[0],mean_confidence_interval(accuracys_1)[1],mean_confidence_interval(accuracys_1)[2]),
                        '{:.2f},[{:.2f},{:.2f}]'.format(mean_confidence_interval(sensitivitys_1)[0],mean_confidence_interval(sensitivitys_1)[1],mean_confidence_interval(sensitivitys_1)[2]),
                        '{:.2f},[{:.2f},{:.2f}]'.format(mean_confidence_interval(specificitys_1)[0],mean_confidence_interval(specificitys_1)[1],mean_confidence_interval(specificitys_1)[2]),]



    data['T1_rad2'] = ['{:.2f},[{:.2f},{:.2f}]'.format(mean_confidence_interval(accuracys_2)[0],mean_confidence_interval(accuracys_2)[1],mean_confidence_interval(accuracys_2)[2]),
                        '{:.2f},[{:.2f},{:.2f}]'.format(mean_confidence_interval(sensitivitys_2)[0],mean_confidence_interval(sensitivitys_2)[1],mean_confidence_interval(sensitivitys_2)[2]),
                        '{:.2f},[{:.2f},{:.2f}]'.format(mean_confidence_interval(specificitys_2)[0],mean_confidence_interval(specificitys_2)[1],mean_confidence_interval(specificitys_2)[2]),]

    data.to_csv(f'/archive/.../output/ensemble_model_{operation}_{date}.csv')

ensemble_model_cv('OR')
ensemble_model_cv('AND')
