#coding: utf-8
'''
Created on May 1, 2013

@author: Giulio

Runs experiments in batch.
'''
from SharedLibs.tracetools import TraceReader
from advance_notice import trim_emergencies, join_emergencies, thermocast_analyze_predictions, xor_analyze_predictions
from forecasting import file_iter

import sys
from filters import AdaptableHoltFilter, AdaptableARFilter
import math
import numpy as np
import matplotlib
import datetime
matplotlib.use('QT4Agg')
import matplotlib.pyplot as pyplot


class ExpRunner(object):
    def __init__(self, trace_path, lo_temp, hi_temp, trace_start_offset, tick_value, hidden_vars_path=None, \
                 weights_path=None, mote_id=None, confirmations=1, delta=60, min_alarm_window=0 * 60, \
                 max_alarm_window=10 * 60):
        '''
        @param trace_path: path to the trace where predictions will be made
        @param lo_temp: lower temperature threshold
        @param hi_temp: higher temperature threshold
        @param trace_start_offset: offset from the start where predictions and emergencies will be considered
        @param tick_value: every data tick corresponds to a number of seconds given by this variable
        @param hidden_vars_path: path to hidden vars file
        @param weights_path: path to weights file
        @param mode_id: id of the mote to perform all calculations
        @param confirmations: number of ticks to consider before triggering an emergency
        @param delta: interval (in seconds) to join fragmented emergencies
        '''
        self.trace_path = trace_path
        self.hidden_vars_path = hidden_vars_path
        self.weights_path = weights_path
        self.hidden_vars = []
        self.weights = []
        self.mote_ids = []

        # Makes sure that all spirit paths are either None or contain stuff
        assert (hidden_vars_path == weights_path == None) or \
               (isinstance(hidden_vars_path, str) and isinstance(weights_path, str))

        # Flag that indicates that we'll need to do use modified version of calc_errors.
        # Spirit mode means that predictions will take place at the hidden variable.
        self.spirit_mode = self.hidden_vars_path is not None

        # When mode_id is None, multivariate mode is assumed. Instead of calculating errors on all motes, a single
        # mote is considered.
        self.mote_id = mote_id

        self.observations = [] # list of temperatures
        self.lo_temp = lo_temp
        self.hi_temp = hi_temp
        self.confirmations = confirmations
        self.delta = delta
        self.trace_start_offset = trace_start_offset
        self.tick_value = tick_value
        self.run_count = 0 # Number of experiments run
        self.trace_start = None
        self.trace_end = None
        self.max_alarm_window = max_alarm_window / tick_value
        self.min_alarm_window = min_alarm_window / tick_value

        # Stores predictions for the last run
        self.predictions_cache = None


    def data_facade(self, data, key):
        if not key:
            return data.values()[1:] # skip timestamp
        return data[key]


    def setup(self):
        '''
        Find emergencies and do some preprocessing.
        '''
        trace_reader = TraceReader(self.trace_path)
        trace_gen = trace_reader.parse()

        # Fills the observation list and finds the trace_start and trace_end
        data = trace_gen.next()
        self.trace_start = data['timestamp'] + self.trace_start_offset # actual trace start
        self.observations.append(self.data_facade(data, self.mote_id))
        for data in trace_gen:
            self.observations.append(self.data_facade(data, self.mote_id))
            self.trace_end = data['timestamp']

        # Fills the hidden_vars list
        if self.spirit_mode:
            with open(self.hidden_vars_path) as file_obj:
                self.mote_ids = file_obj.readline()[1:].split()
                self.hidden_vars = [data[1] for data in file_iter(file_obj)]
            with open(self.weights_path) as file_obj:
                self.weights = [data[1:] for data in file_iter(file_obj)]

        # Finds all emergencies
        self.emergencies = [e for e in self.confirmation_trigger(iter(self.observations), \
                                                                 offset=self.trace_start - self.trace_start_offset)]
        self.emergencies = trim_emergencies(self.trace_start, self.emergencies, self.trace_end)
        self.emergencies = join_emergencies(self.emergencies, self.delta)

        assert len(self.emergencies) > 0


    def calc_errors(self, observations, predictions, lag, trace_start_offset, train_delay):
        '''
        @return: a list with errors
        '''
        errors = []
        for i in xrange(trace_start_offset, len(observations)):
            '''
            observations is in [t_start, t_end]
            predictions  is in [t_start + trace_offset - lag - train_delay, t_end + lag]
            '''
            observation = observations[i]
            prediction = predictions[i - lag - train_delay]

            if not self.mote_id: # multivariate
                error = [observation[j] - prediction[j] for j in xrange(len(observation))]
            else:
                error = observation - prediction
            errors.append(error)
        return errors


    def calc_alarm_forecast(self, predictions, lag, train_delay):
        assert self.hi_temp == self.lo_temp

        alarm_forecasts = []
        curr_forecast = 0
        t_start = self.trace_start - self.trace_start_offset
        confirmations = 0

        for i in xrange(self.trace_start_offset, len(self.observations)):
            if self.observations[i] < self.hi_temp:
                # prediction made for lag periods ahead
                prediction = predictions[i - train_delay]
                if prediction > self.hi_temp:
                    if confirmations == 0:
                        curr_forecast = lag
                    alarm_forecasts.append((t_start + i, curr_forecast))
                    confirmations += 1
                else:
                    if confirmations > 0:
                        confirmations -= 1
                        alarm_forecasts.append((t_start + i, curr_forecast))

                if curr_forecast > 0:
                    curr_forecast -= 1
            else:
                confirmations = 0
                curr_forecast = 0

        return alarm_forecasts


    def calc_alarm_forecast_stats(self, alarm_forecasts):
        # Greater advance notice issued that is close to the actual emergency. Closeness is measured through max_alarm_window.
        best_advances = {em[0]: (0, 0) for em in self.emergencies}

        # These measure the error that each extrapolation has
        mean_lateness = 0.0
        mean_earliness = 0.0
        mean_advance_error = 0.0

        late_alarms = 0
        early_alarms = 0

        for alarm_instant, alarm_advance in alarm_forecasts:
            em_start = self.emergencies[0][0]
            assert len(self.emergencies) == 1

            alarm_offset = em_start - (alarm_instant + alarm_advance)

            if alarm_advance > best_advances[em_start][1] and abs(alarm_offset) < self.max_alarm_window:
                best_advances[em_start] = (alarm_instant, alarm_advance)

            if not (alarm_offset < -self.max_alarm_window * 3):
                error = alarm_offset ** 2
                if alarm_offset >= 0:
                    mean_earliness += error
                    early_alarms += 1
                else:
                    mean_lateness += error
                    late_alarms += 1
                mean_advance_error += error


        mean_advance_time = sum(val[1] for val in best_advances.itervalues()) / len(self.emergencies)
        mean_lateness = math.sqrt(mean_lateness / late_alarms) if late_alarms > 0 else 0
        mean_earliness = math.sqrt(mean_earliness / early_alarms) if early_alarms > 0 else 0
        mean_advance_error = math.sqrt(mean_advance_error / (late_alarms + early_alarms)) \
            if late_alarms + early_alarms > 0 else 0

        return mean_advance_time, mean_lateness, mean_earliness, mean_advance_error, late_alarms, early_alarms


    def calc_stats(self, triggered_emergencies, alarm_forecasts, lag, predictions, train_delay):
        '''
        Calculates all the relevant statistics for the current run.
        '''
        mat = thermocast_analyze_predictions(triggered_emergencies, self.emergencies, lag)
        underdetected_time, overdetected_time, detected_time = xor_analyze_predictions(triggered_emergencies, \
                                                                                       self.emergencies)

        recall = (detected_time  / (detected_time + underdetected_time)) if detected_time + underdetected_time > 0 else 0
        FAR = (overdetected_time / (detected_time + overdetected_time))  if detected_time + overdetected_time > 0 else 0

        #total_detection_time = int(sum(e[2] - e[0] for e in self.emergencies))

        errors = self.calc_errors(self.observations, predictions, lag, self.trace_start_offset, train_delay)

        if not self.mote_id:
            series_count = len(errors)
            errors_count = len(errors[0])
            rmse = np.mean([math.sqrt( np.mean([errors[i][j] ** 2 for j in xrange(errors_count)])) for i in xrange(series_count)])
        else:
            rmse = math.sqrt(sum(e ** 2 for e in errors) / len(errors))

        mean_advance_time, mean_lateness, mean_earliness, mean_advance_error, late_alarms, early_alarms, \
            = self.calc_alarm_forecast_stats(alarm_forecasts)

        return {'mat': mat, 'recall': recall, 'pred_error': rmse, 'mean_adv_time': mean_advance_time, \
                'mean_earliness': mean_earliness, 'mean_lateness': mean_lateness, 'mean_adv_error': mean_advance_error, \
                'late_alarms': late_alarms, 'early_alarms': early_alarms, 'FAR': FAR}


    def confirmation_trigger(self, data_gen, preproc_function=None, preproc_results=None, offset=0):
        '''
        @param preproc_results: a list to keep the results of preproc_function
        '''
        if not preproc_function:
            preproc_function = lambda data, mote_id: data

        confirmations = 0
        emergency_temp = 0
        emergency_start = 0
        emergency_end = 0
        confirmed = False
        i = 0

        while True:
            try:
                data = data_gen.next()
            except StopIteration:
                break

            temp = preproc_function(data, self.mote_id)
            if preproc_results is not None:
                preproc_results.append(temp)

            if temp > self.hi_temp:
                confirmations = min(self.confirmations, confirmations + 1)
                if not confirmed and confirmations == self.confirmations:
                    emergency_temp = temp
                    emergency_start = i * self.tick_value + offset
                    confirmed = True

            elif temp < self.lo_temp:
                confirmations = max(0, confirmations - 1)

            if confirmed and confirmations == 0:
                emergency_end = i * self.tick_value + offset
                yield (emergency_start, emergency_temp, emergency_end)
                confirmed = False
            i += 1

        # Maybe an emergency interval hasn't closed yet. If that's the case, we need to close it.
        if confirmed:
            emergency_end = self.trace_start + i * self.tick_value
            yield (emergency_start, emergency_temp, emergency_end)


    def create_spirit_preproc(self, forecaster):
        '''
        Creates a closure to be used in confirmation_trigger
        '''
        # We need to skip training on weights because data_gen will have iterated over the training period
        weights_iter = iter(self.weights[forecaster.training_delay:]) # skips training

        def spirit_preproc(y, mote_id):
            weights = weights_iter.next()
            predicted_y = forecaster.apply(y)

            reconstructed_data = [predicted_y * weight for weight in weights]

            if mote_id:
                mote_index = self.mote_ids.index(mote_id)
                return reconstructed_data[mote_index]

            return reconstructed_data

        return spirit_preproc


    def run(self, forecaster, lag, plot=False):
        '''
        @param lag: must be in tick units rather than seconds
        '''
        # This check is important to make sure that all the experiments will use the same data
        assert self.trace_start_offset >= forecaster.training_delay + lag

        # Train
        if self.spirit_mode:
            data_gen = iter(self.hidden_vars)
        else:
            data_gen = iter(self.observations)

        for _i in xrange(forecaster.training_delay):
            data = data_gen.next()
            forecaster.apply(data)

        # holds predictions made at the current time to current time + lag
        # these predictions are shifted backwards because of the training delay
        predictions = []

        if self.spirit_mode:
            # this function will predict in SPIRIT and then output real temperature
            predictor_preproc = self.create_spirit_preproc(forecaster)
        else:
            predictor_preproc = lambda data, mote_id: forecaster.apply(data)

        # Process emergencies
        triggered_emergencies = [e for e in self.confirmation_trigger(data_gen, predictor_preproc, predictions, \
                                self.trace_start - self.trace_start_offset + forecaster.training_delay + lag)]
        triggered_emergencies = trim_emergencies(self.trace_start, triggered_emergencies, self.trace_end)
        triggered_emergencies = join_emergencies(triggered_emergencies, self.delta)

        self.run_count += 1

        alarm_forecasts = self.calc_alarm_forecast(predictions, lag, forecaster.training_delay)

        if plot:
            self.plot(predictions, triggered_emergencies, alarm_forecasts, lag, forecaster)

        self.predictions_cache = predictions

        return self.calc_stats(triggered_emergencies, alarm_forecasts, lag, predictions, forecaster.training_delay)


    def print_results(self, stats):
        # mat, recall, FAR, rmse
        #print "MAT                 :", stats[0]
        #print "Recall              :", stats[1]
        #print "FAR                 :", stats[2]
        print "Prediction error     :", stats['pred_error']
        print "Best advance notice  :", stats['mean_adv_time']
        print "Error earliness      : %f (%d)" % (stats['mean_earliness'], stats['early_alarms'])
        print "Error lateness       : %f (%d)" % (stats['mean_lateness'], stats['late_alarms'])
        print "Error adv. notice    :", stats['mean_adv_error']


    def timestamps2dates(self, timestamps):
        return matplotlib.dates.date2num([datetime.datetime.fromtimestamp(ts) for ts in timestamps])


    def plot(self, predictions, triggered_emergencies, alarm_forecasts, lag, forecaster):
        fig = pyplot.figure()
        ax1 = fig.add_subplot(111)
        ax1.grid(True)

        pyplot.xlabel('Tempo (horas:minutos:segundos)')

        train_delay = forecaster.training_delay
        observations = self.observations
        predictions = predictions[:-lag]

        dates = self.timestamps2dates(self.trace_start - self.trace_start_offset + i for i in xrange(len(observations)))

        dark_grey = "#050505"
        p3, = ax1.plot_date(dates, [self.lo_temp] * len(dates), ':', color="black")

        if self.lo_temp != self.hi_temp:
            ax1.plot_date(dates, [self.hi_temp] * len(dates), ':', color="black")

        p1, = ax1.plot_date(dates, observations, '-', color=dark_grey)
        p2, = ax1.plot_date(dates[lag + train_delay:], predictions, '-', color="grey")


        def plot_emergencies(emergency_list, color, style, offset=0.5):
            for emergency_time, _emergency_temp, emergency_end in emergency_list:
                ax1.plot_date(self.timestamps2dates([emergency_time, emergency_end]), \
                                 [self.hi_temp + offset] * 2, style, color=color, linewidth=3)

        # plot real emergencies
        #plot_emergencies(self.emergencies, "red", '-', 0)

        # plot detected emergencies
        #plot_emergencies(triggered_emergencies, "purple", '-', -1)

        pyplot.ylabel(u'Temperatura (ºC)')

        axs = [p2, p1, p3]
        legend_labels = [u'previsões', u'observações', u'limiar de temperatura']
        # plot alarm forecasts
        if alarm_forecasts and False:
            ax2 = ax1.twinx()
            ''
            # ideal curve
            ax2.plot_date(self.timestamps2dates(self.emergencies[0][0] - i \
                                                for i in xrange(self.max_alarm_window, self.min_alarm_window + 1, -1)), \
                          [i for i in xrange(self.max_alarm_window, self.min_alarm_window + 1, -1)], \
                          '--', color='grey', linewidth=1)

            x = [alarm_forecast[0] for alarm_forecast in alarm_forecasts]
            y = [alarm_forecast[1] for alarm_forecast in alarm_forecasts]
            p4 = ax2.plot_date(self.timestamps2dates(x), y, '.', color='grey', linewidth=1)
            ax2.axhline(self.min_alarm_window, color="orange")
            ax2.axhline(self.max_alarm_window, color="orange")
            axs.append(p4)
            legend_labels.append(u'aviso prévio')
            pyplot.ylabel(u'Aviso prévio (s)')
        else:
            print 'No alarm forecasts'

        if hasattr(forecaster, 'param_history'):
            ax2 = ax1.twinx()
            #ax2.set_zorder(9)
            dates = self.timestamps2dates(self.trace_start - self.trace_start_offset + h[0] + lag for h in forecaster.param_history)
            p4, = ax2.plot_date(dates, [h[1][0] for h in forecaster.param_history], '--', color=dark_grey, drawstyle='steps')

            param_history = None
            if isinstance(forecaster, AdaptableHoltFilter):
                param_history = [h[1][1] * 10 for h in forecaster.param_history]
            else:
                param_history = [h[1][1] for h in forecaster.param_history]

            p5, = ax2.plot_date(dates, param_history, '--', color='grey', drawstyle='steps')
            pyplot.ylabel(u'Parâmetros')
            pyplot.ylim((-0.1, 1.1))
            axs.extend([p4, p5])

            if isinstance(forecaster, AdaptableHoltFilter):
                legend_labels.extend([u'alfa', u'beta'])
            else:
                legend_labels.extend([u'phi1', u'phi2'])

        # plot trace_offset
        ax1.axvline(self.timestamps2dates([self.trace_start])[0], color="grey")

        pyplot.legend(axs, legend_labels, loc=2).set_zorder(10)
        #ax1.set_zorder(10)

        pyplot.show()