import numpy as np
import logging

def debug_plot(x, segment_list, create_line_func, plot_title):
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(range(len(x)), x)

    for seg in segment_list:
        plt.scatter(seg, x[seg], s=8)
        plt.plot(seg, create_line_func(x[seg]))
    plt.title(plot_title)
    plt.savefig(plot_title + ".png")
    plt.close()

class TimeSeriesSegmentation(object):
    def __init__(self,max_error):
        self.segment_list = None
        self.x = None
        self.max_error = max_error

    def fit_predict(self,x):
        raise ValueError("not implementated")

    def calculate_error(self,x,y):
        return np.max(np.abs(x-y))

    def plot(self):
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(self.x,"ro")
        for seg in self.segment_list:
            plt.plot(seg[1], seg[0], "+-")
        plt.show()

    def create_line(self, x, method="regression"):
        """
        Fit a line for x
        """
        x = np.array(x)
        n = len(x)

        if method=="simple":
            line = np.linspace(x[0],x[-1],n)
        elif method == "regression":
            line = np.poly1d(np.polyfit(range(n),x,1))(range(n))
        elif method == "poly":
            line = np.poly1d(np.polyfit(range(n),x,2))(range(n))

        return line

class BottomUp(TimeSeriesSegmentation):
    """
    segment signal using sliding bottom up approach
    """

    def fit_predict(self,x):
        """
        Function to fit linear segments based on x
        Args:
            x: input signal
        Returns:
            None
        """
        n = len(x)
        segment_index = [[i, i + 1] for i in range(0, n, 2)]
        error_list = [self.get_merge_cost(x[segment_index[i]], x[segment_index[i+1]]) for i in range(len(segment_index)-1)]

        while True:
            min_error_index = np.argmin(error_list)
            self.merge_next(segment_index, min_error_index)
            
            if len(segment_index) == 3:
                break
            if min_error_index > 0:
                error_list[min_error_index-1] = self.get_merge_cost(x[segment_index[min_error_index - 1]],x[segment_index[min_error_index]])

            if min_error_index < len(error_list) - 1:
                error_list[min_error_index+1] = self.get_merge_cost(x[segment_index[min_error_index]], x[segment_index[min_error_index + 1]])

            error_list.pop(min_error_index)
            
            if len(error_list)!=len(segment_index)-1:
                raise ValueError("error length not right")

            if min(error_list)>self.max_error:
                break

        self.x = x
        self.segment_list=[[self.create_line(x[idx],"regression"), idx] for idx in segment_index]
        
        # self.finalAdjust()
        
    def finalAdjust(self):
        nSeg = len(self.segment_list)
        i = 0
        while i < nSeg - 1:
            new_seg1, new_seg2 = self.adjust_split(self.segment_list[i],self.segment_list[i+1])
            self.segment_list[i] = new_seg1
            self.segment_list[i + 1] = new_seg2
            i += 1

    def adjust_split(self, seg1, seg2):
        # function to find the best split point given seg1 and seg2
        # Args:
        #	seg1: [fitted value, idx]
        # 	seg2: [fitted value, idx]
        # print seg1[1], seg2[1]

        seg_index = seg1[1] + seg2[1]
        segX = self.x[seg_index]
        
        n = len(seg_index)

        min_error = self.max_error * 100
        min_error_index = 1

        for i in range(1, n - 2):
            s1 = segX[:i]
            s2 = segX[i:]
            # print s1, s2
            if len(s1) > 2:
                e1 = self.calculate_error(self.create_line(s1), s1)
            else:
                e1 = 0

            if len(s2) > 2:
                e2 = self.calculate_error(self.create_line(s2), s2)
            else:
                e2 = 0

            if e1 + e2 < min_error:
                min_error = e1 + e2
                min_error_index = i
    
        return [self.create_line(segX[:min_error_index]), seg_index[:min_error_index] ], \
            [self.create_line(segX[min_error_index:]), seg_index[min_error_index:] ]

    def get_merge_cost(self, left_segment, right_segment):
        """
        function to calculate the error when merging the right segment
        Args:
            leftSeg: left segment
            rightSeg: the segment to merge
        Returns:
            error when merging the right segment
        """
        segments = np.concatenate((left_segment, right_segment))
        line = self.create_line(segments)
        return self.calculate_error(line, segments)

    def merge_next(self, segment_list, index):
        """
        function to merge the segment of "index" with its next segment
        Args:
            segment_list: a list of segment
            index: the segment to merge with its right segment
        """
        segment_list[index] = (segment_list[index] + segment_list[index+1]) # merge 
        segment_list.pop(index + 1) # pop the right segment


class SplitAndMerge(BottomUp):
    def fit_predict(self, x):
        n = len(x)
        x = np.array(x)
        segment_index_list = self.random_initialization(n)
        iter = 0

        while iter < n * 5:
            segmentIndexList_step1 = []

            converged = True

            # Split
            for i in range(len(segment_index_list)):
                y = x[segment_index_list[i]]
                y_fit = self.create_line(y)
                error = self.calculate_error(y, y_fit)
                if error > self.max_error:
                    newSegs = self.split(segment_index_list[i], y, y_fit)
                    segmentIndexList_step1 = segmentIndexList_step1 + newSegs
                    converged = False
                else:
                    segmentIndexList_step1.append(segment_index_list[i])

            segmentIndexList_step2 = segmentIndexList_step1.copy()

            # Merge
            if not converged:
                i = 0
                while i < len(segmentIndexList_step2) - 1:

                    mergeRightCost = self.get_merge_cost(x[segmentIndexList_step2[i]], x[segmentIndexList_step2[i + 1]])

                    if mergeRightCost < self.max_error:
                        segmentIndexList_step2[i] = segmentIndexList_step2[i] + segmentIndexList_step2[i + 1]
                        # then pop the right segment
                        segmentIndexList_step2.pop(i + 1)
                    else:
                        i += 1

            # debugPlot(x, segmentIndexList_step2, self.createLine, "itarNum=" + str(iterNum) + "_step2")

            # Adjust
            if not converged:
                segment_index_list = self.splitAdjust_overall(x, segmentIndexList_step2)
            else:
                segment_index_list = segmentIndexList_step2.copy()

            # debugPlot(x, segmentIndexList, self.createLine, "itarNum=" + str(iterNum) + "_step3")
            if converged:
                break
            iter += 1

        if iter == n * 5:
            logging.info("iter maximum reached")
        # get the final results
        self.x = x
        self.segment_list = [[self.create_line(x[segment_index], "regression"), segment_index] for segment_index in segment_index_list]

    def split(self, x, y, y_fit):
        # first find which points are larger than the maximum error
        # function return a list of new segments
        error_points = np.where(abs(y - y_fit) > self.max_error)[0]

        if len(error_points) >= 2:
            # splitPoint = (errorPoints[0] + errorPoints[1]) // 2
            split_point = (error_points[0] + error_points[-1]) // 2
            # splitPoint = len(x) // 2
        else:
            split_point = len(x) // 2

        new_segments = [[x[i] for i in range(split_point)], [x[i] for i in range(split_point, len(x))]]
        return new_segments

    def random_initialization(self, n):
        """
        randomly split the n points into two parts
        """
        random_split_point = np.random.randint(n // 3, 2 * n // 3)
        segment_index_list = [tuple(range(random_split_point)), tuple(range(random_split_point, n))]
        return segment_index_list

    def split_adjustment_overall(self, x, segment_index_list):
        new_segment_index_list = segment_index_list.copy()
        nSeg = len(segment_index_list)
        i = 0
        while i < nSeg - 1:
            new_seg1, new_seg2 = self.split_adjustment(x, new_segment_index_list[i], new_segment_index_list[i + 1])
            new_segment_index_list[i] = new_seg1
            new_segment_index_list[i + 1] = new_seg2
            i += 1
        return new_segment_index_list

    def split_adjustment(self, x, segment_index_list1, segment_index_list2):
        segment_index = segment_index_list1 + segment_index_list2
        segX = x[segment_index]
        min_error = self.max_error * 99999
        min_error_index = None
        n = len(segment_index)

        # if there are only 4 or less points, return original segments
        if len(segment_index) <= 4:
            return segment_index_list1, segment_index_list2

        for i in range(2, n - 1):
            s1 = segX[:i]
            s2 = segX[i:]
            if len(s1) > 2:
                e1 = self.calculate_error(self.create_line(s1), s1)
            else:
                e1 = 0

            if len(s2) > 2:
                e2 = self.calculate_error(self.create_line(s2), s2)
            else:
                e2 = 0

            if max(e1, e2) < min_error:
                min_error = max(e1, e2)
                min_error_index = i

        return (segment_index[:min_error_index], segment_index[min_error_index:])

